import numpy as np

from corta import montar as M

SR = 16000


def audio(partes):
    """partes = [(segundos, amplitude)]: ruído branco nesse volume (0,1 ≈ −20 dB; 0,018 ≈ −35 dB)."""
    rng = np.random.default_rng(7)
    return np.concatenate([(rng.standard_normal(int(d * SR)) * amp).astype(np.float32) for d, amp in partes])


# fala (1,5 s) · pausa (0,8 s) · fala (1,5 s) · pausa (0,8 s) · fala (1,5 s), com 1 s de sala antes e depois
def gravacao(sala):
    return audio([(1.0, sala), (1.5, 0.1), (0.8, sala), (1.5, 0.1), (0.8, sala), (1.5, 0.1), (1.0, sala)])


def test_sala_silenciosa_continua_no_limiar_de_sempre():
    m = M.medir_limiar(gravacao(0.001), SR)                 # sala em −60 dB
    assert m["limiar"] == M.LIMIAR_VOZ_DB and m["ruido"] < -55


def test_sala_com_ruido_sobe_o_limiar_e_acha_as_pausas():
    x = gravacao(0.018)                                     # sala em −35 dB: o caso de 13/11
    m = M.medir_limiar(x, SR)
    assert -36 < m["ruido"] < -33 and -31 < m["limiar"] < -25
    trechos = [[1.0, 7.1]]                                  # o detector de voz achou tudo como uma fala só
    fixo = M._intervalos(trechos, [0], x, SR, True, None, M.LIMIAR_VOZ_DB)
    novo = M._intervalos(trechos, [0], x, SR, True, None, m["limiar"])
    assert len(fixo) == 1                                   # −42 dB: o ruído conta como voz, nenhuma pausa sai
    assert len(novo) == 3                                   # limiar medido: as duas pausas saem
    assert sum(e - s for s, e in novo) < sum(e - s for s, e in fixo) - 0.8


def test_limiar_nunca_chega_perto_da_voz():
    m = M.medir_limiar(gravacao(0.05), SR)                  # sala barulhenta (−26 dB) com voz em −20
    assert m["limiar"] <= m["voz"] - M.VOZ_TETO + 0.01


def test_respiro_no_fim_de_cada_pedaco_so_em_sala_com_ruido():
    x = gravacao(0.018)
    lim = M.medir_limiar(x, SR)["limiar"]
    pecas = M._intervalos([[1.0, 7.1]], [0], x, SR, True, None, lim)
    fins_da_fala = [2.5, 4.8, 7.1]
    for (_, e), f in zip(pecas, fins_da_fala):
        assert M.DEPOIS + M.RESPIRO - 0.03 <= e - f <= M.DEPOIS + M.RESPIRO + 0.03      # ~0,19 s depois da fala
    quieto = gravacao(0.001)
    pecas = M._intervalos([[1.0, 7.1]], [0], quieto, SR, True, None, M.medir_limiar(quieto, SR)["limiar"])
    for (_, e), f in zip(pecas, fins_da_fala):
        assert M.DEPOIS - 0.03 <= e - f <= M.DEPOIS + 0.03                              # sala silenciosa: como antes


def test_respiro_nao_entra_no_trecho_seguinte_nem_passa_do_corte_pedido():
    # fala · 0,12 s · fala de um take tirado: o pedaço mantido não pode trazer o começo do take seguinte
    x = audio([(1.0, 0.018), (1.5, 0.1), (0.12, 0.018), (1.5, 0.1), (1.0, 0.018)])
    lim = M.medir_limiar(x, SR)["limiar"]
    trechos = [[1.0, 2.5], [2.62, 4.12]]
    pecas = M._intervalos(trechos, [0], x, SR, True, None, lim)
    assert pecas[-1][1] <= 2.62 - 0.02 + 1e-6
    pecas = M._intervalos(trechos, [[0, None, 2.0]], x, SR, True, None, lim)            # corte pedido em 2,0 s
    assert pecas[-1][1] <= 2.0 + 1e-6


def test_pausa_no_meio_de_uma_palavra_nao_e_cortada():
    x = gravacao(0.018)
    lim = M.medir_limiar(x, SR)["limiar"]
    palavra = [{"word": "advocacia", "start": 2.3, "end": 3.5}]      # a "pausa" de 2,5–3,3 s cai dentro dela
    sem = M._intervalos([[1.0, 7.1]], [0], x, SR, True, None, lim)
    com = M._intervalos([[1.0, 7.1]], [0], x, SR, True, palavra, lim)
    assert len(sem) == 3 and len(com) == 2
    assert not M._no_meio_de_palavra([{"word": "é", "start": 2.0, "end": 4.0}], 2.5, 3.3)   # palavra de 2 s: é pausa
