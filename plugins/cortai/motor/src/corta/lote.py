"""Lote: prepara, transcreve e lista os trechos de TODOS os vídeos de uma pasta, um depois do outro.

O Claude roda isto em segundo plano e já decide os takes do 1º vídeo enquanto os outros processam
(a parte pesada é do computador; a decisão é do Claude). O andamento fica em
`<pasta>/_corta/lote.json`; vídeo que já tem a lista de trechos não é processado de novo.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from .base import CortaErro, log, salvar_json

EXTENSOES = {".mov", ".mp4", ".m4v", ".mkv", ".avi", ".webm"}
SAIDAS = re.compile(r"\(((?i:editado|legendado|final|zoom[^)]*)|[A-H])\)")   # (A)…(H): lote "cada um diferente"


def videos_da_pasta(pasta: Path) -> list[Path]:
    if not pasta.is_dir():
        raise CortaErro(f"Não achei a pasta {pasta}")
    vs = [p for p in sorted(pasta.iterdir())
          if p.is_file() and p.suffix.lower() in EXTENSOES and not SAIDAS.search(p.stem) and not p.name.startswith(".")]
    if not vs:
        raise CortaErro(f"Nenhum vídeo bruto em {pasta} (mov, mp4, m4v…). Saídas do Cortaí são ignoradas.")
    return vs


def lote(pasta: Path, voz: str, ritmo: str = "rapido", idioma: str = "pt", com_trechos: bool = True) -> dict:
    from .preparar import preparar
    from .transcrever import transcrever
    from .trechos import listar
    pasta = pasta.resolve()
    vs = videos_da_pasta(pasta)
    estado_arq = pasta / "_corta" / "lote.json"
    estado_arq.parent.mkdir(exist_ok=True)
    estado = {"pasta": str(pasta), "videos": {v.name: "na fila" for v in vs}, "inicio": time.time()}
    salvar_json(estado_arq, estado)
    log(f"== lote: {len(vs)} vídeo(s) em {pasta}")
    for n, v in enumerate(vs, 1):
        job = pasta / "_corta" / v.stem
        if (job / "trechos_texto.json").exists() or (not com_trechos and (job / "palavras.json").exists()):
            estado["videos"][v.name] = "pronto"
            log(f"PRONTO {n}/{len(vs)}: {v.name} (já estava feito)")
            salvar_json(estado_arq, estado)
            continue
        try:
            estado["videos"][v.name] = "preparando"
            salvar_json(estado_arq, estado)
            preparar(v, voz=voz, ritmo=ritmo)
            estado["videos"][v.name] = "transcrevendo"
            salvar_json(estado_arq, estado)
            transcrever(v, idioma=idioma)
            if com_trechos:
                estado["videos"][v.name] = "lendo trechos"
                salvar_json(estado_arq, estado)
                listar(v, isolado="auto", idioma=idioma)
            estado["videos"][v.name] = "pronto"
            log(f"PRONTO {n}/{len(vs)}: {v.name}")
        except CortaErro as e:
            estado["videos"][v.name] = f"erro: {e}"
            log(f"ERRO {n}/{len(vs)}: {v.name}: {e}")
        salvar_json(estado_arq, estado)
    estado["fim"] = time.time()
    salvar_json(estado_arq, estado)
    log(f"== lote terminado em {(estado['fim'] - estado['inicio']) / 60:.1f} min")
    return estado
