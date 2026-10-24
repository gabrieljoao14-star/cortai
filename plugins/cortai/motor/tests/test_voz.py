import importlib
import os


def test_alinhamento_vira_palavras():
    from corta.voz import palavras_do_alinhamento
    al = {"characters": list("Oi, tudo bem?"),
          "character_start_times_seconds": [i * 0.1 for i in range(13)],
          "character_end_times_seconds": [i * 0.1 + 0.08 for i in range(13)]}
    ws = palavras_do_alinhamento(al)
    assert [w["word"] for w in ws] == ["Oi,", "tudo", "bem?"]
    assert ws[0]["start"] == 0.0 and ws[1]["start"] == 0.4 and ws[2]["end"] == 1.28


def test_chave_fica_so_no_arquivo_local(tmp_path, monkeypatch):
    monkeypatch.setenv("CORTA_HOME", str(tmp_path))
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    import corta.base, corta.voz
    importlib.reload(corta.base)
    v = importlib.reload(corta.voz)
    assert v.chave() is None
    v._gravar_env({"ELEVENLABS_API_KEY": "sk_teste_1234567890abcdef"})
    assert v.chave() == "sk_teste_1234567890abcdef"
    if os.name != "nt":                                         # no Windows a pasta do usuário já é só dele
        assert (tmp_path / ".env").stat().st_mode & 0o077 == 0     # só o dono lê
    v.desconectar()
    assert v.chave() is None
    monkeypatch.delenv("CORTA_HOME")
    importlib.reload(corta.base)
    importlib.reload(corta.voz)
