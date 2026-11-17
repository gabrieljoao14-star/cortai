"""Etapa 2: monta o vídeo só com o que fica, direto do ORIGINAL, numa passada só.

- Sem `takes.json`: fica toda a fala (só tira silêncio e barulho).
- Com `takes.json` ({"manter": [3, 4, [7, 12.40, null], …]}): fica só o que o Claude e a pessoa decidiram.
  Número = trecho inteiro; [trecho, início, fim] = corta dentro do trecho (null mantém a borda).
- `apertar`: mede pela energia da voz onde cada fala começa e termina e corta pausa interna > 0,22 s,
  sem criar corte < 0,15 s (vira "pulo" de imagem). Ligado por padrão no ritmo rápido.
- O que conta como voz depende da sala: o motor mede o ruído de fundo da gravação e sobe o limiar a
  partir dele (em sala com ruído de −35 dB o limiar fixo de −42 dB não achava pausa nenhuma, 13/11).
- Com o limiar mais alto a fala "termina" mais cedo, então cada pedaço ganha um respiro de até 0,10 s
  a mais no fim (0,19 s no total), sem entrar no trecho seguinte: sem ele a última sílaba ficava curta
  e a palavra sumia na emenda. Em sala silenciosa a sobra continua a de sempre (0,09 s).

Sincronia por construção (nota 01/04): cortes na grade de quadros (cada quadro = N amostras exatas),
vídeo por select=between(n,…) em árvore balanceada e áudio fatiado na amostra com fade de 8 ms.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from .base import (Cronometro, CortaErro, ffmpeg, fps_saida, ler_json, log, nome_seguro, pasta_job, registrar_saida,
                   rodar, saida_livre, salvar_json)
from .perfil import args_video, carregar as carregar_perfil

LIMIAR_VOZ_DB = -42     # sala silenciosa: acima disso é voz (a −45 entra respiração). É o piso do limiar.
BORDA_DB = -45          # para recuperar consoante que o VAD cortou ("Clica" virava "lica")
RUIDO_PERCENTIL = 12    # o ruído da sala é o nível dos 12 % mais baixos da gravação
RUIDO_FOLGA = 8         # o limiar fica 8 dB acima do ruído…
VOZ_FOLGA = 24          # …ou 24 dB abaixo da voz, o que for maior
VOZ_TETO = 10           # e nunca a menos de 10 dB da voz (não pode comer sílaba fraca)
RESPIRO = 0.10          # sobra a mais no fim de cada pedaço em sala com ruído (sem invadir o trecho seguinte)
RESPIRO_CHEIO = 6       # o respiro cresce com o limiar e fica inteiro 6 dB acima do de sala silenciosa
PALAVRA_MAX = 0.9       # pausa no meio de uma palavra mais curta que isso não é pausa
BORDA_MAX = 0.30
JANELA = 0.01
REGIAO_MIN = 0.06       # som mais curto que isso é estalo
PAUSA_MAX = 0.22        # pausa interna maior que isso é cortada
ANTES, DEPOIS = 0.06, 0.09
CORTE_MIN = 0.15
FADE = 0.008


def _db_em(x: np.ndarray, sr: int, t: float) -> float:
    n = int(JANELA * sr)
    seg = x[max(0, int(t * sr)): max(0, int(t * sr)) + n]
    return float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)) if len(seg) else -120.0


def medir_limiar(x: np.ndarray, sr: int) -> dict:
    """Mede o ruído da sala e a voz e devolve o limiar de voz desta gravação.

    Sala silenciosa (ruído em −50 dB): dá −42, igual a antes. Sala com ruído em −35 dB: dá uns −27,
    e as pausas voltam a aparecer. Números conferidos nas 18 gravações de 13/11.
    """
    n = int(JANELA * sr)
    k = len(x) // n
    if k < 50:                                    # menos de 0,5 s: não dá para medir
        return {"limiar": float(LIMIAR_VOZ_DB), "ruido": None, "voz": None}
    db = 20 * np.log10(np.sqrt((x[: k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)
    ruido = float(np.percentile(db, RUIDO_PERCENTIL))
    alto = db[db > ruido + 15]
    voz = float(np.percentile(alto, 50)) if len(alto) else -20.0
    limiar = max(LIMIAR_VOZ_DB, min(max(ruido + RUIDO_FOLGA, voz - VOZ_FOLGA), voz - VOZ_TETO))
    return {"limiar": round(float(limiar), 1), "ruido": round(ruido, 1), "voz": round(voz, 1)}


def _refinar(x, sr, s, e, limiar: float = LIMIAR_VOZ_DB):
    borda = BORDA_DB + (limiar - LIMIAR_VOZ_DB)      # em sala com ruído a borda sobe junto
    t = s
    while t > max(0.0, s - BORDA_MAX) and _db_em(x, sr, t - JANELA) > borda:
        t -= JANELA
    s2 = max(0.0, min(s, t - 0.03))
    t = e
    while t < e + BORDA_MAX and _db_em(x, sr, t) > borda:
        t += JANELA
    return s2, max(e, t + 0.03)


def _no_meio_de_palavra(palavras: list[dict] | None, s: float, e: float) -> bool:
    """A "pausa" entre s e e cai dentro de uma palavra (consoante surda, vogal fraca)?"""
    if not palavras:
        return False
    m = (s + e) / 2
    return any(w["start"] + 0.06 < m < w["end"] - 0.06 and w["end"] - w["start"] < PALAVRA_MAX for w in palavras)


def _regioes(x, sr, a, b, limiar: float = LIMIAR_VOZ_DB, palavras: list[dict] | None = None):
    n = int(JANELA * sr)
    seg = x[int(a * sr): int(b * sr)]
    k = len(seg) // n
    if not k:
        return []
    on = 20 * np.log10(np.sqrt((seg[: k * n].reshape(k, n) ** 2).mean(1)) + 1e-9) > limiar
    out, i = [], 0
    while i < k:
        if on[i]:
            j = i
            while j < k and on[j]:
                j += 1
            out.append([a + i * JANELA, a + j * JANELA])
            i = j
        else:
            i += 1
    juntos = []
    for r in out:
        if juntos and (r[0] - juntos[-1][1] <= PAUSA_MAX or _no_meio_de_palavra(palavras, juntos[-1][1], r[0])):
            juntos[-1][1] = r[1]
        else:
            juntos.append(r)
    return [r for r in juntos if r[1] - r[0] >= REGIAO_MIN]


def _intervalos(trechos, plano, x, sr, apertar: bool, palavras: list[dict] | None = None,
                limiar: float = LIMIAR_VOZ_DB):
    itens = sorted(plano, key=lambda it: it if isinstance(it, int) else it[0])
    brutos, faixas = [], []
    for it in itens:
        i, so, eo = (it, None, None) if isinstance(it, int) else (it[0], it[1], it[2])
        if not 0 <= i < len(trechos):
            raise CortaErro(f"takes.json fala do trecho {i}, mas só existem {len(trechos)} (T000–T{len(trechos) - 1:03d}).")
        faixas.append((so if so is not None else trechos[i][0], eo if eo is not None else trechos[i][1]))
        if apertar:
            # a janela de busca não entra na fala do trecho vizinho (que pode ser um take tirado)
            antes_ = trechos[i - 1][1] + 0.02 if i > 0 else 0.0
            depois_ = trechos[i + 1][0] - 0.02 if i + 1 < len(trechos) else trechos[i][1] + 0.3
            a = so if so is not None else max(0.0, min(trechos[i][0], max(antes_, trechos[i][0] - 0.3)))
            b = eo if eo is not None else max(trechos[i][1], min(depois_, trechos[i][1] + 0.3))
            # o respiro para na borda pedida no takes.json ou 0,05 s antes do trecho seguinte
            teto = eo if eo is not None else max(trechos[i][1], min(b, depois_ - 0.03))
            respiro = RESPIRO * min(1.0, max(0.0, (limiar - LIMIAR_VOZ_DB) / RESPIRO_CHEIO))
            pecas = []
            for s, e in _regioes(x, sr, max(0.0, a), b, limiar, palavras):
                s2, e2 = max(a, s - ANTES), min(b, e + DEPOIS)
                e2 = max(e2, min(e2 + respiro, teto))
                if pecas and s2 - pecas[-1][1] < CORTE_MIN:
                    pecas[-1][1] = e2
                else:
                    pecas.append([s2, e2])
            if pecas:
                brutos.extend(pecas)
                continue
        s, e = _refinar(x, sr, *trechos[i], limiar)
        brutos.append([so if so is not None else s, eo if eo is not None else e])
    # o aperto por volume não pode engolir palavra: em áudio baixo (gravação de reunião) ele cortava
    # "não", "via", "A". Palavra transcrita dentro de um take mantido volta inteira.
    if apertar and palavras:
        for w in palavras:
            meio = (w["start"] + w["end"]) / 2
            for fa, fb in faixas:
                if fa <= meio <= fb:
                    if not any(a <= meio <= b for a, b in brutos):
                        brutos.append([max(fa, w["start"] - 0.04), min(fb, w["end"] + 0.06)])
                    break
    juntos = []
    for s, e in sorted(brutos):
        if juntos and s <= juntos[-1][1] + CORTE_MIN:
            juntos[-1][1] = max(juntos[-1][1], e)
        else:
            juntos.append([max(0.0, s), e])
    return juntos


def _arvore(termos):
    # a soma linear "a+b+c…" estoura o parser do ffmpeg com > ~100 termos
    if len(termos) == 1:
        return termos[0]
    m = len(termos) // 2
    return f"({_arvore(termos[:m])}+{_arvore(termos[m:])})"


def _plano_na_janela(trechos, plano, ini: float, fim: float):
    """Só o que cai dentro de [ini, fim] (cortes de vídeo longo), com as bordas presas à janela."""
    out = []
    for it in plano:
        i, so, eo = (it, None, None) if isinstance(it, int) else (it[0], it[1], it[2])
        s = so if so is not None else trechos[i][0]
        e = eo if eo is not None else trechos[i][1]
        if e <= ini or s >= fim:
            continue
        out.append([i, max(s, ini) if s < ini else so, min(e, fim) if e > fim else eo])
    return out


def montar(video: Path, takes: Path | None = None, apertar: bool | None = None, saida: Path | None = None,
           formato: str | None = None, enquadrar: str = "rosto", zoom: str = "nao",
           janela: tuple[float, float] | None = None, regioes: Path | None = None,
           limiar: float | None = None) -> Path:
    from .enquadrar import filtro as filtro_quadro, planos
    from .rosto import amostras, posicao
    video = video.resolve()
    job = pasta_job(video)
    if not (job / "trechos.json").exists():
        raise CortaErro("Rode primeiro: corta preparar <vídeo>")
    dados = ler_json(job / "trechos.json")
    trechos, info = dados["trechos"], dados["info"]
    plano = ler_json(takes)["manter"] if takes else list(range(len(trechos)))
    if janela:
        plano = _plano_na_janela(trechos, plano, *janela)
        if not plano:
            raise CortaErro(f"Não tem fala entre {janela[0]:.1f} s e {janela[1]:.1f} s.")
    if apertar is None:
        apertar = dados["ritmo"] == "rapido" or janela is not None
    perfil = carregar_perfil()
    F = fps_saida(info["fps"])
    voz, sr = sf.read(job / "voz.wav", dtype="float32", always_2d=True)
    mono = voz.mean(1)
    spf = sr // F

    palavras = ler_json(job / "palavras.json") if (job / "palavras.json").exists() else None
    medida = medir_limiar(mono, sr)
    if limiar is not None:                      # --limiar: a pessoa (ou o Claude) decide o número
        medida["limiar"] = float(limiar)
        log(f"   limiar de voz pedido: {limiar:.0f} dB")
    elif medida["limiar"] > LIMIAR_VOZ_DB + 0.5:
        log(f"   sala com ruído de fundo ({medida['ruido']:.0f} dB): pausa medida abaixo de {medida['limiar']:.0f} dB "
            f"(sala silenciosa usa {LIMIAR_VOZ_DB} dB)")
    intervalos = _intervalos(trechos, plano, mono, sr, apertar, palavras, medida["limiar"])
    if janela:
        intervalos = [[max(s, janela[0] - 0.15), min(e, janela[1] + 0.2)] for s, e in intervalos]
    # o último pedaço não passa do fim do vídeo: a sobra depois da última fala pedia quadros que não
    # existem e o som ficava 2 quadros mais longo que a imagem (C-01, 13/11)
    ultimo = int(min(info["duracao"], len(mono) / sr) * F)
    quadros = [(int(round(s * F)), min(ultimo, int(round(e * F)))) for s, e in intervalos]
    quadros = [(a, b) for a, b in quadros if b > a]
    if not quadros:
        raise CortaErro("Nada para montar: a lista de takes ficou vazia.")

    fade = int(FADE * sr)
    rampa = np.linspace(0, 1, fade, dtype=np.float32)[:, None]
    pedacos, mapa, t_out = [], [], 0.0
    for a, b in quadros:
        p = voz[a * spf: b * spf].copy()
        falta = (b - a) * spf - len(p)
        if falta > 0:
            p = np.vstack([p, np.zeros((falta, p.shape[1]), np.float32)])
        p[:fade] *= rampa
        p[-fade:] *= rampa[::-1]
        pedacos.append(p)
        dur = (b - a) / F
        mapa.append({"original": [a / F, b / F], "saida": [round(t_out, 4), round(t_out + dur, 4)]})
        t_out += dur

    palavras_saida = []
    if palavras:
        for w in palavras:
            meio = (w["start"] + w["end"]) / 2
            for m in mapa:
                s0, e0 = m["original"]
                if s0 <= meio < e0:
                    off = m["saida"][0] - s0
                    palavras_saida.append({"word": w["word"], "start": round(max(s0, w["start"]) + off, 3),
                                           "end": round(min(e0, w["end"]) + off, 3)})
                    break

    # enquadramento e zoom: planos na linha do tempo da saída, rosto medido no original
    cadeia, ow, oh, geo = "", info["largura"], info["altura"], None
    if enquadrar in ("tela-camera", "camera") and formato in (None, "", "original"):
        formato = "9:16"
    precisa_quadro = (formato not in (None, "", "original")) or zoom != "nao"
    if precisa_quadro:
        lista_planos = planos(palavras_saida, [m["saida"] for m in mapa], t_out)
        rostos, reg_tc = [], None
        if enquadrar in ("tela-camera", "camera"):
            from .regioes import carregar as carregar_regioes
            reg_tc = carregar_regioes(video, regioes, janela)
            if zoom != "nao":
                log("   (zoom fica desligado com tela + câmera e só câmera)")
                zoom = "nao"
            rostos = [(0.5, 0.5)] * len(lista_planos)
        elif enquadrar == "rosto":
            grupos = []
            for m in mapa:
                a, b = m["original"]
                if grupos and a - grupos[-1][1] < 8:
                    grupos[-1][1] = b
                else:
                    grupos.append([a, b])
            amos = []
            for a, b in grupos:
                amos += amostras(video, max(0.0, a - 0.25), b + 0.25)
            def para_original(t):
                for m in mapa:
                    if m["saida"][0] <= t < m["saida"][1]:
                        return m["original"][0] + (t - m["saida"][0])
                return mapa[-1]["original"][1]
            achou = 0
            for a, b in lista_planos:
                cx, cy, ok = posicao(amos, para_original(a + 0.05), para_original(max(a + 0.05, b - 0.05)))
                achou += ok
                rostos.append((cx, cy))
            log(f"   rosto encontrado em {achou} de {len(lista_planos)} planos")
        else:
            rostos = [(0.5, 0.5)] * len(lista_planos)
        cadeia, ow, oh, geo = filtro_quadro(info["largura"], info["altura"], formato, enquadrar, zoom, lista_planos, rostos,
                                            reg_tc)

    wav = job / "audio_montado.wav"
    sf.write(wav, np.vstack(pedacos), sr, subtype="PCM_16")
    expr = _arvore([f"between(n,{a},{b - 1})" for a, b in quadros])
    filtro = job / "filtro_select.txt"
    filtro.write_text(f"[0:v:0]fps={F},select='{expr}',setpts=N/{F}/TB{cadeia}[v]", encoding="utf-8")
    saida = saida_livre(Path(saida) if saida else video.with_name(f"{video.stem} (editado).mp4"))
    saida.parent.mkdir(parents=True, exist_ok=True)
    extra = f" · {ow}x{oh}" + (f" · zoom {zoom}" if zoom != "nao" else "") + (f" · {enquadrar}" if precisa_quadro else "")
    log(f"== montando {len(quadros)} pedaços · {t_out:.1f} s · {F} fps{extra} · {perfil['encoder']}")
    c = Cronometro("montagem")
    rodar([ffmpeg(), "-y", "-v", "error", "-hwaccel", "auto", "-i", video, "-i", wav, "-/filter_complex", filtro,
           "-map", "[v]", "-map", "1:a:0", *args_video(perfil), "-r", F,
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", saida], descricao="montagem do vídeo")
    c.fim()
    wav.unlink(missing_ok=True)

    nome = nome_seguro(saida.stem)
    arq_mapa, arq_pal = job / f"mapa_{nome}.json", job / f"palavras_{nome}.json"
    salvar_json(arq_mapa, {"fps": F, "apertar": apertar, "takes": str(takes) if takes else None, "janela": janela,
                           "formato": formato, "enquadrar": enquadrar if precisa_quadro else None, "zoom": zoom, "quadro": geo,
                           "limiar_db": medida["limiar"], "ruido_db": medida["ruido"], "mapa": mapa})
    salvar_json(arq_pal, palavras_saida)
    # compatibilidade: a última montagem também fica nos nomes fixos
    salvar_json(job / "mapa.json", ler_json(arq_mapa))
    salvar_json(job / "palavras_saida.json", palavras_saida)
    registrar_saida(job, {"arquivo": str(saida.resolve()), "etapa": "montar", "palavras": str(arq_pal), "mapa": str(arq_mapa)})
    log(f"   → {saida}")
    return saida
