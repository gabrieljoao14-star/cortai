import numpy as np

from corta.texto_final import comparar, em_linhas, janelas, repetidas


def ws(texto, passo=0.4, inicio=0.0):
    return [{"word": p, "start": round(inicio + i * passo, 2), "end": round(inicio + i * passo + 0.3, 2)}
            for i, p in enumerate(texto.split())]


def test_texto_igual_nao_avisa_nada():
    r = comparar(ws("Hoje eu vou te mostrar como editar."), ws("hoje eu vou te mostrar como editar"))
    assert r["iguais"] == 7 and not (r["sobras"] or r["faltas"] or r["trocas"] or r["repetidas"])


def test_grafia_e_numero_nao_sao_aviso():
    # a legenda tem o texto corrigido pela pessoa; o Whisper ouve "lerite" e "noventa e sete" de novo
    r = comparar(ws("o holerite custa 97 reais no Claude"), ws("o lerite custa noventa e sete reais no Cloud"))
    assert not (r["sobras"] or r["faltas"] or r["trocas"])


def test_fala_de_bastidor_aparece_como_sobra():
    r = comparar(ws("clique no botão abaixo agora mesmo"), ws("clique no botão abaixo pode cortar aí agora mesmo"))
    assert len(r["sobras"]) == 1 and r["sobras"][0]["texto"] == "pode cortar aí" and not r["sobras"][0]["emenda"]
    assert abs(r["sobras"][0]["em"] - 1.6) < 0.01


def test_uma_palavra_so_conta_se_for_na_emenda():
    esperado, ouvido = ws("isso muda tudo no seu processo"), ws("isso muda e tudo no seu processo")
    assert comparar(esperado, ouvido)["sobras"] == []                    # longe de corte: ruído do Whisper
    r = comparar(esperado, ouvido, emendas=[0.9])                        # em cima do corte: resto de take
    assert len(r["sobras"]) == 1 and r["sobras"][0]["texto"] == "e" and r["sobras"][0]["emenda"]


def test_palavra_engolida_na_emenda_aparece_como_falta():
    r = comparar(ws("o prazo acabou ontem doutor"), ws("o prazo ontem doutor"), emendas=[0.8])
    assert len(r["faltas"]) == 1 and r["faltas"][0]["texto"] == "acabou" and r["faltas"][0]["emenda"]
    r = comparar(ws("o prazo acabou de vez ontem doutor"), ws("o prazo ontem doutor"))   # 3 palavras: avisa em qualquer lugar
    assert r["faltas"][0]["texto"] == "acabou de vez"


def test_palavra_cortada_na_emenda_aparece_como_troca():
    r = comparar(ws("a citação é nula sim"), ws("a ação é nula sim"), emendas=[0.5])
    assert not r["trocas"]                                               # "ação" × "citação": parecidas, é grafia
    r = comparar(ws("o juiz multou o banco"), ws("o juiz ou o banco"), emendas=[0.8])
    assert r["trocas"] == [{"em": 0.8, "ate": 1.1, "texto": "ou", "esperado": "multou"}]
    assert comparar(ws("o juiz multou o banco"), ws("o juiz ou o banco"))["trocas"] == []      # longe de corte: grafia


def test_recomeco_que_ficou_aparece_como_repetida():
    r = repetidas(ws("hoje eu vou hoje eu vou te mostrar como editar"))
    assert len(r) == 1 and r[0]["texto"] == "hoje eu vou" and abs(r[0]["de_novo_em"] - 1.2) < 0.01
    # 4 palavras de novo alguns segundos depois também
    r = repetidas(ws("o banco tem que devolver em dobro e mais uma coisa o banco tem que devolver tudo"))
    assert len(r) == 1 and r[0]["texto"] == "o banco tem que devolver"
    # repetição curta e distante (refrão de 3 palavras) não é aviso; nem a mesma frase 1 min depois
    assert repetidas(ws("você não precisa pagar nada e também você não precisa esperar")) == []
    assert repetidas(ws("toque em saiba mais agora") + ws("toque em saiba mais agora", inicio=60.0)) == []


def test_janelas_cortam_na_pausa_e_cobrem_tudo():
    sr, rng = 16000, np.random.default_rng(1)
    x = (rng.standard_normal(sr * 70) * 0.1).astype(np.float32)
    x[int(28.5 * sr): int(29.0 * sr)] = 0.0001                            # pausa perto dos 30 s
    j = janelas(x)
    assert j[0][0] == 0.0 and abs(j[-1][1] - 70.0) < 0.01
    assert all(abs(a[1] - b[0]) < 1e-9 for a, b in zip(j, j[1:]))
    assert 28.4 <= j[0][1] <= 29.1
    assert janelas(x[: sr * 20]) == [(0.0, 20.0)]


def test_texto_em_linhas_por_janela():
    o = [{**w, "janela": 0} for w in ws("oi tudo bem")] + [{**w, "janela": 1} for w in ws("até mais", inicio=65.0)]
    assert em_linhas(o) == ["0:00  oi tudo bem", "1:05  até mais"]
