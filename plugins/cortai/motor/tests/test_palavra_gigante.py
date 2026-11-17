"""A palavra gigante tem que caber na largura do quadro (13/11: "MULTADO" estourou).

O tamanho é calculado no Remotion (motion/src/efeitos/Textos.tsx). Este teste lê a fórmula de lá e mede
as palavras com a mesma fonte, para a conta e o desenho não se separarem.
"""
import re
from pathlib import Path

from PIL import ImageFont

RAIZ = Path(__file__).resolve().parents[2]
TSX = (RAIZ / "motion" / "src" / "efeitos" / "Textos.tsx").read_text(encoding="utf-8")
FONTE = RAIZ / "motion" / "public" / "fontes" / "montserrat-900-normal.ttf"
W = 1080


def formula():
    m = re.search(r"const tam = Math\.min\(width \* ([\d.]+), \(width \* ([\d.]+)\) / Math\.max\(3, texto\.length \* ([\d.]+)\)\);", TSX)
    assert m, "a fórmula do tamanho da palavra gigante mudou de formato: atualize este teste"
    return tuple(float(x) for x in m.groups())


def largura(texto, teto, larg, por_letra):
    tam = min(W * teto, (W * larg) / max(3, len(texto) * por_letra))
    fonte = ImageFont.truetype(str(FONTE), int(round(tam)))
    return fonte.getlength(texto.upper()) + 2 * tam * 0.06          # + o contorno dos dois lados


def test_palavras_em_maiusculas_cabem_no_quadro():
    f = formula()
    for palavra in ("MULTADO", "DOBRO", "GRÁTIS", "BLOQUEADO", "HONORÁRIOS", "INDENIZAÇÃO", "EM DOBRO", "MAMÃE", "COMMODITY"):
        assert largura(palavra, *f) <= W * 0.96, palavra


def test_a_conta_antiga_estourava():
    # 0,90 de largura e 0,62 por letra (até a 0.6.2): "MULTADO" passava da tela
    assert largura("MULTADO", 0.22, 0.9, 0.62) > W
    assert formula()[1:] == (0.86, 0.84)


def test_subtitulo_tem_tamanho_minimo_legivel():
    assert "Math.max(tam * 0.26, width * 0.05)" in TSX
