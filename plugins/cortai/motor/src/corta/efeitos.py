"""Efeitos de motion (Remotion) por cima do vídeo: palavra gigante, lista, contador, nome e cargo,
manchetes, gráfico, seta e círculo, emoji.

efeitos.json (tempos no relógio do vídeo que vai ser legendado — veja com `corta texto`):
  {"efeitos": [{"tipo": "contador", "em": 12.3, "duracao": 2.5,
                "props": {"de": 0, "ate": 7000, "prefixo": "R$ ", "rotulo": "devolvido em dobro"}},
               {"tipo": "palavra-gigante", "em": 20.0, "duracao": 2.0, "atras": true, "props": {"texto": "dobro"}}]}
"atras": true coloca o efeito atrás da pessoa (recorte do MODNet). Combina com palavra gigante sem fundo
escurecido, posicionada na altura do peito/cabeça.

Posição: o motor mede o rosto naquele momento e põe o efeito no maior espaço livre (acima da
cabeça ou entre o queixo e a legenda), diminuindo até 72 %. Se não couber, vira um "momento
grande" em tela cheia com o fundo escurecido. Regra validada nos Stories do Dr. Cláudio (14/10).
Cada efeito é renderizado uma vez (cache por conteúdo) em vídeo com transparência.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from .base import PASTA_USUARIO, RAIZ_PLUGIN, CortaErro, ler_json, log, salvar_json

MOTION = RAIZ_PLUGIN / "motion"
TIPOS = {"palavra-gigante", "nome-cargo", "manchetes", "lista", "contador", "grafico", "seta-circulo", "emoji", "imagem"}
TOPO_LIVRE = 0.16          # nada nos 16 % de cima (interface do Reels)
# momentos grandes: a legenda some de baixo enquanto estão na tela (senão o texto aparece duas vezes)
ESCONDE_LEGENDA = {"palavra-gigante", "contador", "grafico", "manchetes"}
ESCALA_MIN = 0.72


def _altura(tipo: str, p: dict) -> float | None:
    """Altura aproximada do efeito (fração da altura do quadro) em escala 1. None = tela cheia ou posição própria."""
    if tipo == "palavra-gigante":
        return 0.24 + (0.05 if p.get("subtitulo") else 0)
    if tipo == "nome-cargo":
        return 0.11
    if tipo == "lista":
        return 0.09 + 0.068 * len(p.get("itens") or [1, 2, 3]) + (0.06 if p.get("titulo") else 0)
    if tipo == "contador":
        return 0.17 + (0.05 if p.get("rotulo") else 0)
    if tipo == "grafico":
        return 0.44
    if tipo == "imagem":
        return p.get("_altura_rel", 0.3) + (0.06 if p.get("legenda") else 0)
    return None


def embutir_imagem(props: dict, largura: int, altura: int, base: Path | None = None) -> dict:
    """`arquivo` (foto da pasta da pessoa) → `src` embutido (o Remotion não lê arquivo solto do computador)."""
    import base64
    import io
    from PIL import Image, ImageOps
    p = dict(props)
    arq = Path(p.pop("arquivo", "") or "")
    if not arq.is_absolute() and base:
        arq = base / arq
    if not arq.is_file():
        raise CortaErro(f"Não achei a imagem {arq} (efeito imagem: passe \"arquivo\" com o caminho da foto).")
    im = ImageOps.exif_transpose(Image.open(arq))
    alfa = im.convert("RGBA").getchannel("A") if im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info else None
    buf = io.BytesIO()
    if alfa is not None and alfa.getextrema()[0] < 250:
        # produto já recortado (PNG transparente): aparece solto, com sombra, sem moldura
        im = im.convert("RGBA").crop(alfa.point(lambda a: 255 if a > 8 else 0).getbbox())
        im.thumbnail((1200, 1200))
        im.save(buf, "PNG")
        p["src"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        p["recorte"] = True
    else:
        im = im.convert("RGB")
        im.thumbnail((1200, 1200))
        im.save(buf, "JPEG", quality=88)
        p["src"] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    p["proporcao"] = round(im.height / im.width, 4)
    w = min(largura * 0.72 * float(p.get("tamanho", 1)), altura * 0.5 / p["proporcao"])
    p["_altura_rel"] = round(w * p["proporcao"] / altura + 0.02, 4)
    p["_largura_rel"] = round(w / largura, 4)
    return p


def posicionar(tipo: str, props: dict, rosto: tuple[float, float, float] | None, topo_legenda: float) -> dict:
    """Devolve props com y/escala (ou fundo escurecido) para não cobrir o rosto."""
    p = dict(props)
    if "y" in p or tipo in ("manchetes", "seta-circulo"):
        return p
    if tipo == "emoji":
        if rosto and "pos" not in p:
            cx, cy, fh = rosto
            p["pos"] = {"x": min(0.85, cx + 0.3) if cx < 0.6 else max(0.15, cx - 0.3), "y": max(0.22, cy - fh * 0.6)}
        return p
    h = _altura(tipo, p)
    if h is None or rosto is None:
        return p
    cx, cy, fh = rosto
    cima = (TOPO_LIVRE, max(TOPO_LIVRE, cy - fh * 0.8 - 0.01))          # acima do cabelo
    baixo = (min(topo_legenda, cy + fh * 0.65 + 0.01), topo_legenda - 0.01)  # do queixo até a legenda
    # acima da cabeça é o melhor lugar quando cabe quase inteiro (não encosta na legenda)
    if (cima[1] - cima[0]) >= h * 0.85:
        faixa = cima
    else:
        faixa = max((cima, baixo), key=lambda f: f[1] - f[0])
    espaco = faixa[1] - faixa[0]
    escala = min(1.0, espaco / h)
    if escala >= (0.45 if tipo == "imagem" else ESCALA_MIN):    # foto não tem letra para ler: pode ficar menor
        p["escala"] = round(escala, 3)
        p["y"] = round(faixa[0] + (espaco - h * escala) / 2, 4)
    elif tipo == "imagem" and (lado := _ao_lado(p, h, rosto, topo_legenda)):
        p.update(lado)                          # flutuando ao lado do rosto, sem cobrir
    else:
        # momento grande com o fundo escurecido (a legenda some): o painel vai para baixo do queixo, até a
        # zona segura de baixo, para o rosto continuar à vista. Sem espaço, fica no meio e passa pelo rosto.
        p.setdefault("fundo", "escurecer")
        y0, fim = max(cy + fh * 0.7, 0.42), 0.80
        escala = min(1.0, (fim - y0) / h)
        if escala >= 0.6 and tipo in ("lista", "grafico", "contador"):
            p["escala"] = round(escala, 3)
            p["y"] = round(y0, 4)
    return p


def _ao_lado(p: dict, h: float, rosto: tuple[float, float, float], topo_legenda: float) -> dict | None:
    """Foto ao lado do rosto, do lado com mais espaço. None se ficaria pequena demais (< 30 %)."""
    cx, cy, fh = rosto
    meia = fh * (16 / 9) * 0.42 + 0.02                # meia largura do rosto (fração da largura), com folga
    esq, dir_ = cx - meia - 0.02, 1 - (cx + meia) - 0.02
    espaco = max(esq, dir_)
    w = p.get("_largura_rel", 0.72)
    escala = min(0.6, espaco / w, (topo_legenda - 0.01 - TOPO_LIVRE) / h)
    if escala < 0.3:
        return None
    centro = (cx + meia + 0.01 + w * escala / 2) if dir_ >= esq else (cx - meia - 0.01 - w * escala / 2)
    y = min(max(TOPO_LIVRE, cy - h * escala / 2), topo_legenda - 0.01 - h * escala)
    return {"escala": round(escala, 3), "y": round(y, 4), "x": round(0.5 + (centro - 0.5) / escala, 4)}  # o motor diminui a partir do meio


def _npx() -> str:
    for nome in ("npx", "npx.cmd"):
        achado = shutil.which(nome)
        if achado:
            return achado
    for c in (PASTA_USUARIO / "node" / "bin" / "npx", PASTA_USUARIO / "node" / "npx.cmd"):
        if c.exists():
            return str(c)
    raise CortaErro("A parte de motion não está instalada neste computador (falta o Node). Rode /cortai:instalar.")


_versao = None


def versao_motion() -> str:
    """Impressão digital do código do Remotion: plugin atualizado grava os efeitos de novo (o cache é por
    conteúdo e não via a mudança no desenho)."""
    global _versao
    if _versao is None:
        h = hashlib.sha1()
        for f in sorted((MOTION / "src").rglob("*.ts*")):
            h.update(f.read_bytes())
        _versao = h.hexdigest()[:12]
    return _versao


def renderizar(tipo: str, props: dict, largura: int, altura: int, fps: int, duracao: float, pasta: Path) -> Path:
    if tipo not in TIPOS:
        raise CortaErro(f"Efeito '{tipo}' não existe. Efeitos: {', '.join(sorted(TIPOS))}")
    if not (MOTION / "node_modules" / "remotion").exists():
        raise CortaErro("A parte de motion do plugin não está instalada (node_modules). Rode /cortai:instalar.")
    tudo = {**props, "tipo": tipo, "largura": largura, "altura": altura, "fps": fps, "duracao": round(duracao, 3)}
    chave = hashlib.sha1((json.dumps(tudo, sort_keys=True, ensure_ascii=False) + versao_motion()).encode()).hexdigest()[:16]
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{tipo}_{chave}.mov"
    if destino.exists():
        return destino
    arq_props = pasta / f"{tipo}_{chave}.json"
    salvar_json(arq_props, tudo)
    npx = _npx()
    ambiente = dict(os.environ)
    ambiente["PATH"] = str(Path(npx).parent) + os.pathsep + ambiente.get("PATH", "")   # Node portátil do Cortaí
    r = subprocess.run([npx, "remotion", "render", "src/index.ts", "Efeito", str(destino), f"--props={arq_props}",
                        "--codec=prores", "--prores-profile=4444", "--pixel-format=yuva444p10le", "--image-format=png",
                        "--log=error"], cwd=str(MOTION), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=ambiente)
    if r.returncode != 0 or not destino.exists():
        raise CortaErro(f"O efeito '{tipo}' não renderizou.\n{(r.stderr or r.stdout)[-1500:]}")
    return destino


def preparar_efeitos(arquivo: Path, video: Path, info: dict, destaque: str, topo_legenda: float, pasta: Path) -> list[dict]:
    """Lê efeitos.json, posiciona pelo rosto e renderiza. Devolve [{arquivo, em, duracao, tipo}]."""
    from .base import saida_registrada, fps_saida
    from .rosto import amostras, posicao
    lista = ler_json(arquivo)
    lista = lista.get("efeitos", lista) if isinstance(lista, dict) else lista
    reg = saida_registrada(video) or {}
    mapa, original = None, video
    if reg.get("mapa") and Path(reg["mapa"]).exists():
        mapa = ler_json(reg["mapa"])["mapa"]
        original = Path(ler_json(Path(reg["mapa"]).parent / "trechos.json")["video"])

    def para_original(t: float) -> float:
        if not mapa:
            return t
        for m in mapa:
            if m["saida"][0] <= t < m["saida"][1]:
                return m["original"][0] + t - m["saida"][0]
        return mapa[-1]["original"][1]

    F = fps_saida(info["fps"])
    feitos = []
    for e in lista:
        tipo, em, dur = e["tipo"], float(e["em"]), float(e.get("duracao", 2.5))
        rosto = None
        if info["altura"] > info["largura"] and tipo not in ("manchetes", "seta-circulo"):
            a = para_original(em + min(0.5, dur / 2))
            amos = amostras(original, max(0.0, a - 0.5), a + 0.5)
            cx, cy, ok = posicao(amos, a - 0.5, a + 0.5)
            alturas = [x[3] for x in amos if x[3]]
            if ok and alturas:
                rosto = (cx, cy, sorted(alturas)[len(alturas) // 2])
        if tipo == "imagem":
            e = {**e, "props": embutir_imagem(e.get("props") or {}, info["largura"], info["altura"], Path(arquivo).parent)}
        if e.get("atras") and rosto:
            # atrás da pessoa: a palavra fica grande na altura da cabeça, sem escurecer (o corpo a cobre em parte)
            cx, cy, fh = rosto
            props = {"destaque": destaque, **(e.get("props") or {}), "y": round(max(TOPO_LIVRE, cy - fh * 1.1), 4)}
            props.pop("fundo", None)
        else:
            props = posicionar(tipo, {"destaque": destaque, **(e.get("props") or {})}, rosto, topo_legenda)
        mov = renderizar(tipo, props, info["largura"], info["altura"], F, dur, pasta)
        onde = "tela cheia escurecida" if props.get("fundo") == "escurecer" else (f"y {props['y']:.2f}, escala {props.get('escala', 1):.2f}" if "y" in props else "posição padrão")
        pessoa = None
        if e.get("atras"):
            # "atrás da pessoa": recorta quem fala nesses segundos e coloca por cima do efeito
            from .recorte import recortar
            chave_p = hashlib.sha1(f"{video}|{em:.3f}|{dur:.3f}|{F}".encode()).hexdigest()[:12]
            pessoa = recortar(video, em, dur, F, pasta / f"pessoa_{chave_p}.mov")
            onde += " · atrás da pessoa"
        log(f"   efeito {tipo} em {em:.1f} s ({dur:.1f} s) · {onde}")
        feitos.append({"arquivo": mov, "em": em, "duracao": dur, "tipo": tipo, "pessoa": pessoa,
                       "esconde": tipo in ESCONDE_LEGENDA or props.get("fundo") == "escurecer"})
    return feitos


def motion_instalado() -> bool:
    try:
        _npx()
    except CortaErro:
        return False
    return (MOTION / "node_modules" / "remotion").exists()
