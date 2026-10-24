"""Emoji automático na legenda (estilo "com emoji" ou ajuste emoji=sim): um emoji em cima do bloco quando
aparece uma palavra-chave, no máximo um a cada ~4 s (mais que isso vira poluição).

Imagens: Noto Emoji (Apache 2.0) em assets/emoji, iguais no Mac e no Windows.
"""
from __future__ import annotations

import unicodedata
from functools import lru_cache

from PIL import Image

from ..base import RAIZ_PLUGIN

PASTA = RAIZ_PLUGIN / "assets" / "emoji"
INTERVALO = 4.0

# começo da palavra (sem acento, minúsculo) → código do emoji. Do mais específico para o mais geral.
PALAVRAS = [
    ("dinheir", "1f4b0"), ("reais", "1f4b0"), ("real", "1f4b0"), ("lucr", "1f4b0"), ("ganh", "1f4b0"), ("money", "1f4b0"),
    ("pag", "1f4b8"), ("gast", "1f4b8"), ("prejuiz", "1f4b8"), ("perd", "1f4b8"), ("divid", "1f4b8"),
    ("cartao", "1f4b3"), ("banco", "1f3e6"), ("emprest", "1f3e6"),
    ("gratis", "1f381"), ("present", "1f381"), ("bonus", "1f381"), ("brinde", "1f381"),
    ("erro", "274c"), ("errad", "274c"), ("nunca", "274c"), ("proib", "274c"),
    ("cert", "2705"), ("aprovad", "2705"), ("pront", "2705"), ("resolv", "2705"),
    ("atencao", "26a0"), ("cuidado", "26a0"), ("perigo", "26a0"), ("risco", "26a0"), ("alerta", "1f6a8"), ("golpe", "1f6a8"),
    ("urgent", "1f6a8"), ("fogo", "1f525"), ("quent", "1f525"), ("bomb", "1f525"), ("viral", "1f525"),
    ("rapid", "26a1"), ("energ", "26a1"), ("amor", "2764"), ("coracao", "2764"), ("paix", "2764"),
    ("saude", "1fa7a"), ("medic", "1fa7a"), ("doutor", "1fa7a"), ("remedio", "1f48a"), ("vitamina", "1f48a"),
    ("justica", "2696"), ("lei", "2696"), ("juiz", "2696"), ("advog", "2696"), ("direito", "2696"), ("process", "2696"),
    ("casa", "1f3e0"), ("imovel", "1f3e0"), ("carro", "1f697"), ("viag", "2708"), ("aviao", "2708"),
    ("ideia", "1f4a1"), ("dica", "1f4a1"), ("segredo", "1f92b"), ("cresc", "1f4c8"), ("aument", "1f4c8"), ("venda", "1f4c8"),
    ("vend", "1f6d2"), ("compr", "1f6d2"), ("cai", "1f4c9"), ("queda", "1f4c9"), ("celular", "1f4f1"), ("app", "1f4f1"),
    ("foco", "1f3af"), ("meta", "1f3af"), ("objetiv", "1f3af"), ("duvida", "1f914"), ("pergunt", "2753"), ("porque", "1f914"),
    ("olhem", "1f440"), ("mundo", "1f30e"), ("trabalh", "1f4bc"), ("empresa", "1f4bc"), ("negocio", "1f4bc"),
    ("estud", "1f4da"), ("livro", "1f4da"), ("aprend", "1f9e0"), ("cerebro", "1f9e0"), ("mente", "1f9e0"),
    ("comid", "1f354"), ("fome", "1f354"), ("trein", "1f4aa"), ("academia", "1f4aa"), ("forca", "1f4aa"), ("forte", "1f4aa"),
    ("music", "1f3b5"), ("foguete", "1f680"), ("lanc", "1f680"), ("decol", "1f680"), ("morr", "1f480"), ("mort", "1f480"),
    ("lind", "1f60d"), ("triste", "1f622"), ("chor", "1f62d"), ("raiva", "1f621"), ("odio", "1f621"),
    ("obrigad", "1f64f"), ("deus", "1f64f"), ("parabens", "1f389"), ("festa", "1f389"), ("comemor", "1f973"),
    ("venc", "1f3c6"), ("campe", "1f3c6"), ("conquist", "1f3c6"), ("resultado", "1f3c6"), ("crianc", "1f476"), ("filh", "1f476"),
    ("bebe", "1f476"), ("seguranc", "1f512"), ("senha", "1f511"), ("chave", "1f511"), ("entreg", "1f4e6"), ("produto", "1f4e6"),
    ("foto", "1f4f8"), ("cem", "1f4af"), ("100", "1f4af"), ("perfeit", "1f4af"), ("parceri", "1f91d"), ("acordo", "1f91d"),
    ("contrat", "1f4c4"), ("document", "1f4c4"), ("anot", "1f4dd"), ("escrev", "1f4dd"), ("comenta", "1f4ac"), ("mensag", "1f4ac"),
    ("pessoas", "1f465"), ("cliente", "1f465"), ("equipe", "1f465"), ("ruim", "1f44e"),
    ("incrivel", "1f92f"), ("chocant", "1f92f"), ("absurd", "1f92f"), ("anunci", "1f4e2"), ("aviso", "1f4e2"), ("kkk", "1f602"),
    ("engracad", "1f602"),
    # genéricas por último: só entram se o bloco não tiver nada mais específico
    ("prazo", "23f0"), ("tempo", "23f0"), ("hora", "23f0"), ("minut", "23f0"), ("data", "1f4c5"), ("dia", "1f4c5"),
]
CURTAS = {"lei", "dia", "cai", "app", "cem", "100", "real", "kkk"}   # só a palavra exata


def _normal(w: str) -> str:
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if c.isalnum() and unicodedata.category(c) != "Mn")


def emoji_de(palavras: list[str]) -> str | None:
    """A palavra-chave mais específica do bloco decide (a ordem de PALAVRAS é a prioridade)."""
    ns = [n for n in (_normal(w) for w in palavras) if len(n) >= 2]
    for chave, cod in PALAVRAS:
        if any((n == chave) if chave in CURTAS else n.startswith(chave) for n in ns):
            return cod
    return None


@lru_cache(maxsize=64)
def imagem(cod: str, px: int) -> Image.Image | None:
    arq = PASTA / f"{cod}.png"
    if not arq.exists():
        return None
    return Image.open(arq).convert("RGBA").resize((px, px), Image.LANCZOS)


def escolher(tl: list[dict]) -> list[str | None]:
    """Emoji de cada bloco da linha do tempo, respeitando o intervalo mínimo."""
    out, ultimo = [], -99.0
    for b in tl:
        cod = emoji_de(b["palavras"]) if b["inicio"] - ultimo >= INTERVALO else None
        if cod:
            ultimo = b["inicio"]
        out.append(cod)
    return out
