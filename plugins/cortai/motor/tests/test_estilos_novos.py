from corta.legenda.desenho import Desenhista
from corta.legenda.emoji import emoji_de, escolher
from corta.legenda.estilos import carregar_estilo


def test_emoji_prioriza_palavra_especifica():
    assert emoji_de(["da", "Hora", "do", "Advogado"]) == "2696"
    assert emoji_de(["se", "o", "dinheiro"]) == "1f4b0"
    assert emoji_de(["dia"]) == "1f4c5"
    assert emoji_de(["diante", "disso"]) is None          # "dia" só como palavra inteira


def test_emoji_respeita_intervalo():
    tl = [{"inicio": t, "palavras": ["dinheiro"]} for t in (0.0, 1.0, 4.5)]
    assert escolher(tl) == ["1f4b0", None, "1f4b0"]


def test_estilos_novos_desenham():
    for nome in ("maquina-de-escrever", "hierarquia", "editorial", "com-emoji"):
        est = carregar_estilo(nome)
        d = Desenhista(est, 1080, 1920)
        for ativa in (None, 0, 2):
            img = d.bloco(["aquele", "aposentado", "que", "chega"], ativa, "1f4b0")
            assert img.size == (1080, d.faixa_h)
            assert img.getbbox() is not None
        assert d.px == d.px_base                          # o tamanho volta ao normal depois do bloco


def test_maquina_mostra_so_o_que_foi_dito():
    d = Desenhista(carregar_estilo("maquina-de-escrever"), 1080, 1920)
    uma = d.bloco(["aquele", "aposentado", "que", "chega"], 0).getbbox()
    todas = d.bloco(["aquele", "aposentado", "que", "chega"], 3).getbbox()
    assert (uma[2] - uma[0]) < (todas[2] - todas[0])


def test_junta_valores_separados():
    from corta.legenda.blocos import unir_hifens
    ws = [{"word": w, "start": i, "end": i + 0.5} for i, w in enumerate(["R", "$", "2", ".700", ",00", "e", "10", "%", "e", "-mail"])]
    assert [w["word"] for w in unir_hifens(ws)] == ["R$ 2.700,00", "e", "10%", "e-mail"]


def test_frase_inventada_em_silencio():
    import numpy as np
    from types import SimpleNamespace
    from corta.transcrever import _inventada
    audio = np.concatenate([np.full(16000, 0.2, np.float32), np.full(16000, 0.001, np.float32)])
    ref = float(np.sqrt(np.mean(audio ** 2)))
    assert _inventada(SimpleNamespace(text=" Obrigado.", start=1.1, end=1.9), audio, 0.0, ref, 16000)
    assert not _inventada(SimpleNamespace(text=" Obrigado.", start=0.1, end=0.9), audio, 0.0, ref, 16000)
    assert not _inventada(SimpleNamespace(text=" Eu não contratei", start=1.1, end=1.9), audio, 0.0, ref, 16000)
