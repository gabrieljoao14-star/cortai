"""Versão instalada × versão mais nova no GitHub, e se o instalador já rodou para esta versão.

A skill roda `corta versao` antes de editar:
- ESTADO: instalar  → o plugin foi atualizado mas o instalador não rodou nesta pasta (as animações e o
  atalho ficam na pasta da versão): rode o instalador antes de editar;
- ESTADO: atualizar → existe versão mais nova no GitHub: avise a pessoa (a edição pode seguir);
- ESTADO: ok.
A consulta ao GitHub tem limite de 3 s e fica guardada por 12 h; sem internet, segue sem avisar.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

from .base import PASTA_USUARIO, RAIZ_PLUGIN, ler_json, log, salvar_json

URL_GITHUB = "https://raw.githubusercontent.com/gabrieljoao14-star/cortai/main/plugins/cortai/.claude-plugin/plugin.json"
GUARDAR_HORAS = 12


def versao_instalada() -> str:
    arq = RAIZ_PLUGIN / ".claude-plugin" / "plugin.json"
    try:
        return ler_json(arq)["version"]
    except (OSError, ValueError, KeyError):
        from . import __version__
        return __version__


def _numero(v: str) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except ValueError:
        return (0,)


def versao_github() -> str | None:
    cache = PASTA_USUARIO / "versao_github.json"
    if cache.exists():
        try:
            d = ler_json(cache)
            if time.time() - d["quando"] < GUARDAR_HORAS * 3600:
                return d["versao"]
        except (ValueError, KeyError):
            pass
    try:
        with urllib.request.urlopen(URL_GITHUB, timeout=3) as r:
            v = json.loads(r.read().decode("utf-8"))["version"]
    except Exception:
        return None
    try:
        salvar_json(cache, {"versao": v, "quando": time.time()})
    except OSError:
        pass
    return v


def instalacao_completa() -> bool:
    """O instalador grava a pasta da versão em ~/.corta/instalado.txt quando termina com TUDO CERTO."""
    marca = PASTA_USUARIO / "instalado.txt"
    if marca.exists():
        feita = marca.read_text(encoding="utf-8").strip().lstrip("\ufeff")
        return os.path.normcase(os.path.normpath(feita)) == os.path.normcase(os.path.normpath(str(RAIZ_PLUGIN)))
    # instalações de antes da marca: atalho apontando para esta pasta e animações preparadas
    atalho = PASTA_USUARIO / "bin" / ("corta.cmd" if os.name == "nt" else "corta")
    try:
        aponta = os.path.normcase(str(RAIZ_PLUGIN)) in os.path.normcase(atalho.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        aponta = False
    return aponta and (RAIZ_PLUGIN / "motion" / "node_modules" / "remotion").exists()


def versao() -> str:
    atual = versao_instalada()
    log(f"Cortaí {atual} em {RAIZ_PLUGIN}")
    if not instalacao_completa():
        log("⚠ esta versão ainda não foi preparada neste computador (o plugin foi atualizado sem o instalador)")
        log("ESTADO: instalar")
        return "instalar"
    nova = versao_github()
    if nova and _numero(nova) > _numero(atual):
        log(f"⚠ versão nova disponível: {nova} (esta é {atual}). Para atualizar, cole no Claude Code o prompt "
            f"\"Atualizar\" da aba Instalar do app (https://cortai.dvbusiness.online).")
        log("ESTADO: atualizar")
        return "atualizar"
    log("✅ versão mais nova" if nova else "(sem internet para conferir se há versão nova)")
    log("ESTADO: ok")
    return "ok"
