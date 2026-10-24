"""Queima a legenda no vídeo: desenha cada estado (bloco + palavra ativa + animação) como imagem,
monta uma lista com a duração de cada uma e cola por cima do vídeo com o ffmpeg numa passada.

As palavras vêm, em ordem de preferência: --palavras; a montagem que gerou este vídeo
(tempos já remapeados); a transcrição deste próprio vídeo.
"""
from __future__ import annotations

import math
import os
import re
import shutil
from pathlib import Path

from PIL import Image

from ..base import (Cronometro, CortaErro, conferir_arquivo_local, ffmpeg, info_video, ler_json, log, pasta_job,
                    registrar_saida, nome_seguro, rodar, saida_livre, saida_registrada, salvar_json)
from ..perfil import args_video, carregar as carregar_perfil
from .blocos import linha_do_tempo, montar_blocos
from .desenho import Desenhista
from .estilos import carregar_estilo

TRILHA_VOLUME = 0.32   # trilha em -20 LUFS × 0,32 ≈ -30 LUFS, bem abaixo da voz (-16)
DUR_ANIM = {"pop": 0.18, "pulo": 0.32, "aparecer": 0.20, "subir": 0.22, "nenhuma": 0.0}
PASSO_ANIM = 1 / 30


def achar_palavras(video: Path, palavras: Path | None, idioma: str) -> tuple[list[dict], str]:
    if palavras:
        return ler_json(palavras), str(palavras)
    reg = saida_registrada(video)
    if reg and reg.get("palavras") and Path(reg["palavras"]).exists():
        return ler_json(reg["palavras"]), reg["palavras"]
    job = pasta_job(video.resolve())
    if (job / "palavras.json").exists() and not (job / "mapa.json").exists():
        return ler_json(job / "palavras.json"), str(job / "palavras.json")
    # guarda a transcrição direta: a prévia de cada estilo e o legendar depois usam a mesma (antes cada
    # prévia transcrevia de novo: 2–3 min por estilo no teste de 23/10)
    cache, arq_marca = job / "palavras_direto.json", job / "palavras_direto.marca.json"
    marca = [video.stat().st_size, int(video.stat().st_mtime), idioma]
    if cache.exists() and arq_marca.exists() and ler_json(arq_marca) == marca:
        return ler_json(cache), str(cache)
    from ..transcrever import transcrever_direto
    log("   este vídeo não passou pela montagem: transcrevendo o áudio dele (uma vez só)")
    ws = transcrever_direto(video, idioma)
    salvar_json(cache, ws)
    salvar_json(arq_marca, marca)
    return ws, str(cache)


def _eventos(est: dict, tl: list[dict], des: Desenhista, pasta: Path):
    """Lista (início, fim, arquivo) cobrindo os momentos com legenda."""
    cache: dict = {}
    n_img = [0]

    def salvar(img: Image.Image) -> str:
        nome = f"{n_img[0]:05d}.png"
        img.save(pasta / nome, compress_level=1)
        n_img[0] += 1
        return nome

    emojis = [None] * len(tl)
    if est.get("emoji") in (True, "sim"):
        from .emoji import escolher
        emojis = escolher(tl)

    def estado(bi: int, ativa: int | None) -> str:
        if est["tipo_destaque"] == "nenhum" and not est.get("revelar"):
            ativa = None
        if (bi, ativa) not in cache:
            cache[(bi, ativa)] = (des.bloco(tl[bi]["palavras"], ativa, emojis[bi]), None)
        img, nome = cache[(bi, ativa)]
        if nome is None:
            nome = salvar(img)
            cache[(bi, ativa)] = (img, nome)
        return nome

    ev = []
    dur_anim = DUR_ANIM[est["animacao"]]
    for bi, b in enumerate(tl):
        t = b["inicio"]
        anim_fim = min(b["inicio"] + dur_anim, b["fim"])
        if dur_anim:
            n = max(1, math.ceil((anim_fim - t) / PASSO_ANIM))
            estado(bi, 0)
            base = cache[(bi, 0 if est["tipo_destaque"] != "nenhum" or est.get("revelar") else None)][0]
            for j in range(n):
                t0 = t + j * PASSO_ANIM
                t1 = min(anim_fim, t0 + PASSO_ANIM)
                if t1 - t0 > 0.001:
                    ev.append((t0, t1, salvar(des.animar(base, (j + 1) / n))))
            t = anim_fim
        for k, (a, z) in enumerate(b["ativos"]):
            a, z = max(a, t), min(z, b["fim"])
            if z - a > 0.001:
                ev.append((a, z, estado(bi, k)))
    return ev, n_img[0]


def _job(video: Path) -> Path:
    """Os dados ficam na pasta do vídeo ORIGINAL: a pasta de entrega (ex.: a dos cortes) fica limpa."""
    reg = saida_registrada(video)
    if reg and reg.get("job") and Path(reg["job"]).exists():
        return Path(reg["job"])
    return pasta_job(video)


def _preparar(video: Path, estilo: str, ajustes: dict, palavras: Path | None, idioma: str):
    video = video.resolve()
    conferir_arquivo_local(video)
    info = info_video(video)
    est = carregar_estilo(estilo, ajustes)
    ws, origem = achar_palavras(video, palavras, idioma)
    if not ws:
        raise CortaErro("Não há palavras para legendar (a transcrição veio vazia).")
    blocos = montar_blocos(ws, est["palavras"])
    tl = linha_do_tempo(blocos, info["duracao"])
    des = Desenhista(est, info["largura"], info["altura"])
    # layout tela + câmera: a legenda vai para a faixa do meio (a não ser que a pessoa peça outra posição)
    reg = saida_registrada(video) or {}
    if "posicao" not in (ajustes or {}) and reg.get("mapa") and Path(reg["mapa"]).exists():
        geo = ler_json(reg["mapa"]).get("quadro") or {}
        if geo.get("y_legenda"):
            des.centralizar_em(geo["y_legenda"])
    return video, info, est, tl, des, origem


def _topo_cabeca(video: Path, ate: float) -> float | None:
    """Ponto mais alto da cabeça (fração da altura) enquanto o gancho está na tela, medido no próprio vídeo.
    Teste de 23/10: com a pessoa enquadrada alta, o gancho de 3 linhas cobria a testa."""
    from ..rosto import amostras
    try:
        amos = [a for a in amostras(video, 0.0, ate) if a[1] is not None]
    except CortaErro:
        return None
    if not amos:
        return None
    return max(0.2, min(a[2] - a[3] * 0.85 for a in amos) - 0.015)


def _lista_concat(pasta: Path, ev, duracao: float, vazio: str) -> Path:
    linhas = ["ffconcat version 1.0"]
    t = 0.0
    for a, z, nome in ev:
        if a - t > 0.001:
            linhas += [f"file '{vazio}'", f"duration {a - t:.4f}"]
        linhas += [f"file '{nome}'", f"duration {z - max(a, t):.4f}"]
        t = z
    linhas += [f"file '{vazio}'", f"duration {max(0.04, duracao - t + 1):.4f}", f"file '{vazio}'"]
    lista = pasta / f"lista_{vazio.split('.')[0]}.ffconcat"
    lista.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return lista


def _juntar(intervalos: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out: list[list[float]] = []
    for a, b in sorted(intervalos):
        if out and a <= out[-1][1] + 0.05:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def _fim_primeira_frase(tl: list[dict], padrao: float = 3.5) -> float:
    """Onde o gancho sai: fim da 1ª pergunta se ela vier cedo; senão 3,5 s (entre 2,5 e 4,5 s)."""
    for b in tl:
        if b["inicio"] > 4.5:
            break
        if b["palavras"] and b["palavras"][-1].endswith("?"):
            return b["fim"]
    return padrao


def legendar(video: Path, estilo: str = "creator-bold", ajustes: dict | None = None, palavras: Path | None = None,
             idioma: str = "pt", saida: Path | None = None, gancho: str | None = None, gancho_ate: float | None = None,
             cta: str | None = None, cta_em: float | None = None, barra: bool = False, sons: str = "nao",
             trilha: str | None = None, trilha_arquivo: Path | None = None, efeitos: Path | None = None) -> Path:
    from .extras import Camada, eventos as eventos_topo, faixa_de_sons, viradas
    sem_legenda = estilo in ("nenhuma", "nenhum", "sem")
    video, info, est, tl, des, origem = _preparar(video, "creator-bold" if sem_legenda else estilo, ajustes or {}, palavras, idioma)
    job = _job(video)
    pasta = job / f"_legenda_{nome_seguro(video.stem)}"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True)
    W, H, dur = info["largura"], info["altura"], info["duracao"]
    if gancho and gancho_ate is None:
        gancho_ate = min(4.5, max(2.5, _fim_primeira_frase(tl)))
    if gancho and gancho_ate > 5.0:
        log(f"   gancho até {gancho_ate:.1f} s é longo demais (lido num relance): ficou em 5 s")
        gancho_ate = 5.0
    if gancho and len(gancho.replace("|", " ").split()) > 12:
        log("   ⚠ gancho com mais de 12 palavras: no celular ninguém lê. Encurte se der.")
    partes = ["sem legenda" if sem_legenda else f"legenda '{est['nome']}'"]
    partes += [nome for nome, ligado in (("gancho", gancho), ("CTA", cta), ("barra", barra)) if ligado]
    if sons != "nao":
        partes.append(f"sons {sons}")
    if trilha not in (None, "", "nao") or trilha_arquivo:
        partes.append(f"trilha {trilha or 'própria'}")
    if efeitos:
        partes.append("efeitos")
    log(f"== {' · '.join(partes)} · palavras de: {origem}")
    c = Cronometro("desenho")
    entradas, filtros, rotulo = [], [], "[0:v]"
    n_entrada = lambda: 1 + sum(1 for x in entradas if x == "-i")   # índice da próxima entrada (0 = vídeo)
    lista_fx = []
    if efeitos:
        # efeitos de motion por baixo da legenda (a legenda tem que continuar legível)
        from ..efeitos import preparar_efeitos
        topo_leg = (des.y_centro - des.px * 1.4) / H if not sem_legenda else 0.76
        lista_fx = preparar_efeitos(Path(efeitos), video, info, est["destaque"] if est["destaque"] != est["cor"] else "#FFE14D",
                                    topo_leg, job / "efeitos")
        for k, fx in enumerate(lista_fx):
            idx = n_entrada()
            entradas += ["-itsoffset", f"{fx['em']:.3f}", "-i", fx["arquivo"]]
            fim = fx["em"] + fx["duracao"]
            filtros.append(f"[{idx}:v]format=yuva444p[fx{k}];{rotulo}[fx{k}]overlay=0:0:format=auto:eof_action=pass:"
                           f"enable='between(t,{fx['em']:.3f},{fim:.3f})'[vfx{k}]")
            rotulo = f"[vfx{k}]"
            if fx.get("pessoa"):
                idp = n_entrada()
                entradas += ["-itsoffset", f"{fx['em']:.3f}", "-i", fx["pessoa"]]
                filtros.append(f"[{idp}:v]format=yuva444p[ps{k}];{rotulo}[ps{k}]overlay=0:0:format=auto:eof_action=pass:"
                               f"enable='between(t,{fx['em']:.3f},{fim:.3f})'[vps{k}]")
                rotulo = f"[vps{k}]"
        partes_log = f"   {len(lista_fx)} efeito(s) de motion"
        log(partes_log)
        if gancho and lista_fx:
            # efeito dentro do gancho: os dois disputavam o topo. O gancho sai quando o efeito entra.
            primeiro = min(fx["em"] for fx in lista_fx)
            if primeiro < gancho_ate:
                gancho_ate = max(1.5, primeiro)
                log(f"   gancho sai em {gancho_ate:.1f} s para o efeito entrar (evite efeito nos primeiros segundos)")
    if not sem_legenda:
        ev, n = _eventos(est, tl, des, pasta)
        from ..efeitos import ESCONDE_LEGENDA
        janelas_fx = [(fx["em"], fx["em"] + fx["duracao"]) for fx in lista_fx if fx.get("esconde", fx["tipo"] in ESCONDE_LEGENDA)]
        if cta:          # o CTA fica no lugar da legenda (os dois juntos se sobrepunham no teste de 23/10)
            janelas_fx.append((cta_em if cta_em is not None else max(0.0, dur - 4.0), dur + 1))
        janelas_fx += [tuple(j) for j in (saida_registrada(video) or {}).get("sem_legenda", [])]   # cenas da só animação
        if janelas_fx:
            corte = []
            for a, z, nm in ev:                     # tira da legenda os pedaços que caem num momento grande
                partes_ev = [(a, z)]
                for fa, fz in janelas_fx:
                    nova = []
                    for pa, pz in partes_ev:
                        if pz <= fa or pa >= fz:
                            nova.append((pa, pz))
                        else:
                            if pa < fa:
                                nova.append((pa, fa))
                            if pz > fz:
                                nova.append((fz, pz))
                    partes_ev = nova
                corte += [(pa, pz, nm) for pa, pz in partes_ev if pz - pa > 0.001]
            ev = corte
        if gancho and est["posicao"] == "topo":
            ev = [(a, z, nm) for a, z, nm in ev if a >= gancho_ate]   # legenda no topo espera o gancho sair
        Image.new("RGBA", (W, des.faixa_h), (0, 0, 0, 0)).save(pasta / "vazio.png")
        idx = n_entrada()
        entradas += ["-f", "concat", "-safe", "0", "-i", _lista_concat(pasta, ev, dur, "vazio.png")]
        filtros.append(f"[{idx}:v]format=rgba[leg];{rotulo}[leg]overlay=x=0:y={des.y_faixa}:shortest=1:format=auto[v1]")
        rotulo = "[v1]"
        log(f"   legenda: {n} imagens")
    camada = Camada(est, W, H)
    if gancho and H > W:
        camada.limite_gancho = _topo_cabeca(video, gancho_ate or 3.5)
    cta_ini = None
    if gancho or cta:
        ev_topo = eventos_topo(camada, pasta, dur, gancho, gancho_ate or 0.0, cta, cta_em)
        if cta:
            cta_ini = cta_em if cta_em is not None else max(0.0, dur - 4.0)
        Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(pasta / "vazio_topo.png")
        idx = n_entrada()
        entradas += ["-f", "concat", "-safe", "0", "-i", _lista_concat(pasta, ev_topo, dur, "vazio_topo.png")]
        # a camada cobre a tela inteira: só mistura nos momentos do gancho e do CTA (o resto passa direto)
        janelas = [f"between(t,{a:.3f},{b:.3f})" for a, b in _juntar([(a, z) for a, z, _ in ev_topo])]
        quando = "+".join(janelas) or "0"
        filtros.append(f"[{idx}:v]format=rgba[topo];{rotulo}[topo]overlay=0:0:shortest=1:format=auto:enable='{quando}'[v2]")
        rotulo = "[v2]"
        log(f"   gancho/CTA: {len(ev_topo)} imagens")
    if barra:
        from ..base import fps_saida
        bh = max(6, int(H * 0.006))
        F = fps_saida(info["fps"])
        filtros.append(f"{rotulo}drawbox=x=0:y=0:w=iw:h={bh}:color=black@0.35:t=fill[vb];"
                       f"color=c=0x{camada.destaque.lstrip('#')}:s={W}x{bh}:r={F}[bar];"
                       f"[vb][bar]overlay=x='-w+w*t/{dur:.3f}':y=0:shortest=1[v3]")
        rotulo = "[v3]"
    filtros.append(f"{rotulo}format=yuv420p[v]")
    audio = ["-map", "0:a?", "-c:a", "copy"]
    reg = saida_registrada(video) or {}
    planos = []
    if reg.get("mapa") and Path(reg["mapa"]).exists():
        planos = (ler_json(reg["mapa"]).get("quadro") or {}).get("planos", [])
    pontos, faixas_extra = [], []
    if sons != "nao":
        if gancho:
            pontos.append((0.0, "impacto"))
        if cta:
            pontos.append((cta_ini, "pop"))
        for t in viradas(planos, sons):
            # nada de whoosh depois que o CTA entra: o CTA é o último momento do vídeo
            if (not gancho or t > (gancho_ate or 0) + 0.5) and (cta_ini is None or t < cta_ini - 1):
                pontos.append((t, "whoosh"))
        if pontos:
            arq_sons = faixa_de_sons(dur, pontos, pasta / "sons.wav")
            faixas_extra.append(("sons", n_entrada()))
            entradas += ["-i", arq_sons]
            log(f"   sons: {', '.join(f'{nm} em {t:.1f} s' for t, nm in sorted(pontos))}")
    if trilha not in (None, "", "nao") or trilha_arquivo:
        from ..trilha import gerar as gerar_trilha, preparar_arquivo
        arq_trilha = pasta / "trilha.wav"
        if trilha_arquivo:
            preparar_arquivo(Path(trilha_arquivo), dur, arq_trilha)
            log(f"   trilha: música da pessoa ({Path(trilha_arquivo).name})")
        else:
            impactos = [t for t in viradas(planos, "poucos") if (not gancho or t > (gancho_ate or 0) + 0.5)
                        and (cta_ini is None or t < cta_ini - 1)]
            gerar_trilha(trilha, dur, arq_trilha, gancho_ate=gancho_ate or 0.0, impactos=impactos, cta_em=cta_ini)
        faixas_extra.append(("trilha", n_entrada()))
        entradas += ["-i", arq_trilha]
    if faixas_extra:
        # voz na frente; trilha bem abaixo (~-30 LUFS) e abaixando sozinha quando a pessoa fala
        partes, mix = ["[0:a]asplit=2[voz][chave]"], ["[voz]"]
        for nome, k in faixas_extra:
            if nome == "trilha":
                partes.append(f"[{k}:a]volume={TRILHA_VOLUME}[trb];[trb][chave]sidechaincompress=threshold=0.02:ratio=6:"
                              f"attack=30:release=450:makeup=1[tr]")
                mix.append("[tr]")
            else:
                mix.append(f"[{k}:a]")
        if not any(n == "trilha" for n, _ in faixas_extra):
            partes[0] = "[0:a]anull[voz]"
        partes.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first[a]")
        filtros.append(";".join(partes))
        audio = ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    c.fim()

    perfil = carregar_perfil()
    if saida is None:
        # "X (editado) (2)" → "X (legendado) (2)": o número da versão fica no fim
        nome = video.stem.replace(" (editado)", "")
        m = re.match(r"^(.*?)((?: \(\d+\))*)$", nome)
        saida = video.with_name(f"{m.group(1)} ({'final' if sem_legenda else 'legendado'}){m.group(2)}.mp4")
    saida = saida_livre(Path(saida))
    grafo = pasta / "filtros.txt"
    grafo.write_text(";".join(filtros), encoding="utf-8")
    c = Cronometro("gravação")
    rodar([ffmpeg(), "-y", "-v", "error", "-i", video, *entradas, "-/filter_complex", grafo,
           "-map", "[v]", *audio, *args_video(perfil), "-movflags", "+faststart", saida],
          descricao="gravar vídeo com legenda")
    c.fim()
    arq_blocos = job / f"legenda_{nome_seguro(Path(saida).stem)}.json"
    salvar_json(arq_blocos, {"estilo": None if sem_legenda else est, "blocos": [] if sem_legenda else tl, "saida": str(saida),
                             "gancho": gancho, "gancho_ate": gancho_ate, "cta": cta, "cta_em": cta_ini, "barra": barra,
                             "sons": sorted(pontos), "trilha": trilha_arquivo and str(trilha_arquivo) or trilha})
    reg = saida_registrada(video) or {}
    registrar_saida(job, {"arquivo": str(Path(saida).resolve()), "etapa": "legendar", "estilo": None if sem_legenda else est["id"],
                          "palavras": origem if Path(origem).exists() else None, "mapa": reg.get("mapa"),
                          "origem": str(video), "blocos": str(arq_blocos),
                          # a conferência não compara imagem onde algo grande cobre o quadro de propósito: efeitos,
                          # gancho e CTA (no Windows o CTA sozinho já deu falso desvio de 3 quadros, 24/10)
                          "efeitos_janelas": [[round(fx["em"], 3), round(fx["em"] + fx["duracao"], 3)] for fx in lista_fx]
                          + ([[0.0, round(gancho_ate or 0.0, 3)]] if gancho else [])
                          + ([[round(cta_ini, 3), round(dur + 1, 3)]] if cta and cta_ini is not None else [])})
    if not os.environ.get("CORTA_MANTER"):          # CORTA_MANTER=1 guarda as imagens para diagnóstico
        shutil.rmtree(pasta, ignore_errors=True)
    log(f"   → {saida}")
    return saida


def previa(video: Path, estilo: str = "creator-bold", ajustes: dict | None = None, palavras: Path | None = None,
           idioma: str = "pt", em: float | None = None) -> Path:
    """3 quadros lado a lado com a legenda aplicada, para aprovar antes de gravar o vídeo inteiro."""
    video, info, est, tl, des, _ = _preparar(video, estilo, ajustes or {}, palavras, idioma)
    job = _job(video)
    if em is not None:
        escolhidos = [min(range(len(tl)), key=lambda i: abs(tl[i]["inicio"] - em))]
    else:
        escolhidos = sorted({0, len(tl) // 2, len(tl) - 1})
    quadros = []
    for bi in escolhidos:
        b = tl[bi]
        k = min(1, len(b["ativos"]) - 1)
        a, z = b["ativos"][k]
        t = (a + z) / 2
        arq = job / f"_quadro_{bi}.png"
        rodar([ffmpeg(), "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", arq], descricao="quadro")
        fundo = Image.open(arq).convert("RGBA")
        from .emoji import emoji_de
        cod = emoji_de(b["palavras"]) if est.get("emoji") in (True, "sim") else None
        ativa = k if est["tipo_destaque"] != "nenhum" or est.get("revelar") else None
        fundo.alpha_composite(des.bloco(b["palavras"], ativa, cod), (0, des.y_faixa))
        quadros.append(fundo)
        arq.unlink(missing_ok=True)
    esc = 0.5 if info["altura"] > info["largura"] else 0.4
    w, h = int(info["largura"] * esc), int(info["altura"] * esc)
    folha = Image.new("RGB", (w * len(quadros) + 20 * (len(quadros) - 1), h), (20, 20, 24))
    for i, q in enumerate(quadros):
        folha.paste(q.convert("RGB").resize((w, h), Image.LANCZOS), (i * (w + 20), 0))
    destino = job / f"previa_{nome_seguro(video.stem)}_{est['id']}.png"
    folha.save(destino)
    log(f"   prévia → {destino}")
    return destino
