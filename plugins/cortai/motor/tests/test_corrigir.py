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


def test_pontuacao_fica_no_lugar_quando_troca_varias_palavras():
    # 13/11: trocar a ordem levava a vírgula junto com a palavra
    out, n = _aplicar(ws("olha aqui, doutor. Agora"), ["aqui", "doutor"], ["doutor", "aqui"], None)
    assert n == 1 and [w["word"] for w in out] == ["olha", "doutor,", "aqui.", "Agora"]
    assert out[1]["start"] == 1.0 and out[2]["end"] == 2.8          # o tempo de cada lugar não muda


def test_pontuacao_escrita_do_lado_certo_vale():
    out, _ = _aplicar(ws("doutor aqui agora"), ["doutor", "aqui"], ["doutor,", "aqui."], None)
    assert [w["word"] for w in out] == ["doutor,", "aqui.", "agora"]
    out, _ = _aplicar(ws("isso certo. E"), ["certo"], ["certo?"], None)       # não dobra: "certo?." nunca
    assert out[1]["word"] == "certo?"
    out, _ = _aplicar(ws("e aí, aposentado."), ["aposentado"], ["seu", "João!"], None)
    assert [w["word"] for w in out] == ["e", "aí,", "seu", "João!"]


def test_exato_troca_ao_pe_da_letra():
    base = "o advogado. E o advogado ganhou"
    out, n = _aplicar(ws(base), ["advogado.", "E"], ["advogado,", "e"], None, exato=True)
    assert n == 1 and [w["word"] for w in out] == ["o", "advogado,", "e", "o", "advogado", "ganhou"]
    out, n = _aplicar(ws(base), ["advogado."], ["advogado"], None, exato=True)   # tira o ponto
    assert n == 1 and out[1]["word"] == "advogado"
    assert _aplicar(ws(base), ["Advogado."], ["x"], None, exato=True)[1] == 0     # maiúscula conta


def test_contexto_troca_so_antes_da_proxima():
    base = "chegou ao fim. Mas não é o fim. E pronto"
    out, n = _aplicar(ws(base), ["fim."], ["fim,"], None, proxima="Mas", exato=True)
    assert n == 1 and [w["word"] for w in out] == "chegou ao fim, Mas não é o fim. E pronto".split()
    out, n = _aplicar(ws(base), ["fim"], ["final"], None, proxima="e")           # sem --exato: ignora maiúscula e ponto
    assert n == 1 and out[7]["word"] == "final." and out[2]["word"] == "fim."
    assert _aplicar(ws("o fim"), ["fim"], ["x"], None, proxima="Mas")[1] == 0     # última palavra não tem próxima


def test_nao_troca_duas_vezes_o_mesmo_lugar_e_guarda_dados_extras():
    out, n = _aplicar(ws("a a a"), ["a", "a"], ["b", "b"], None)
    assert n == 1 and [w["word"] for w in out] == ["b", "b", "a"]
    pal = [{"word": "lerite,", "start": 0.0, "end": 0.5, "trecho": 4}]
    out, _ = _aplicar(pal, ["lerite"], ["holerite"], None)
    assert out == [{"word": "holerite,", "start": 0.0, "end": 0.5, "trecho": 4}]
