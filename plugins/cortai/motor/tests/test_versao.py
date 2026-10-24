import importlib
import json


def _recarregar(monkeypatch, home, raiz):
    monkeypatch.setenv("CORTA_HOME", str(home))
    monkeypatch.setenv("CORTA_RAIZ", str(raiz))
    import corta.base, corta.versao
    importlib.reload(corta.base)
    return importlib.reload(corta.versao)


def test_estados(tmp_path, monkeypatch):
    home, raiz = tmp_path / "home", tmp_path / "plugin"
    (raiz / ".claude-plugin").mkdir(parents=True)
    (raiz / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": "0.6.2"}))
    home.mkdir()
    v = _recarregar(monkeypatch, home, raiz)
    assert v.versao_instalada() == "0.6.2"
    assert v.versao() == "instalar"                              # plugin novo sem instalador
    (home / "instalado.txt").write_text("﻿" + str(raiz) + "\n", encoding="utf-8")
    monkeypatch.setattr(v, "versao_github", lambda: "0.6.10")
    assert v.versao() == "atualizar"                             # 0.6.10 > 0.6.2 (número, não texto)
    monkeypatch.setattr(v, "versao_github", lambda: None)
    assert v.versao() == "ok"                                    # sem internet não trava
    monkeypatch.delenv("CORTA_HOME")
    monkeypatch.delenv("CORTA_RAIZ")
    import corta.base
    importlib.reload(corta.base)
    importlib.reload(v)
