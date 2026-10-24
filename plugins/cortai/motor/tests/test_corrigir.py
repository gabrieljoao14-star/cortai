from corta.corrigir import _aplicar


def ws(texto):
    return [{"word": p, "start": i * 1.0, "end": i * 1.0 + 0.8} for i, p in enumerate(texto.split())]


def test_pontuacao_ignorada_na_busca_e_preservada():
    out, n = _aplicar(ws("clica aqui, faz sua"), ["aqui"], ["agora"], None)
    assert n == 1 and out[1]["word"] == "agora,"
    out, n = _aplicar(ws("clica aqui, faz sua"), ["aqui,"], ["agora"], None)
    assert n == 1 and out[1]["word"] == "agora,"


def test_insercao_vira_palavras_separadas_com_tempo_dividido():
    out, n = _aplicar(ws("aquele aposentado que"), ["aquele", "aposentado"], ["Sabe", "aquele", "aposentado"], None)
    assert n == 1 and [w["word"] for w in out] == ["Sabe", "aquele", "aposentado", "que"]
    assert out[0]["start"] == 0.0 and out[2]["end"] == 1.8
    assert all(a["end"] <= b["start"] + 1e-6 for a, b in zip(out, out[1:]))


def test_em_troca_so_a_ocorrencia_mais_perto():
    out, n = _aplicar(ws("isso e isso e isso"), ["isso"], ["aquilo"], 2.1)
    assert n == 1 and [w["word"] for w in out] == ["isso", "e", "aquilo", "e", "isso"]


def test_correcao_que_comeca_com_hifen():
    out, n = _aplicar(ws("má -fé"), ["-fé"], ["fé"], None)
    assert n == 1 and out[1]["word"] == "fé"
