"""Voz com a ElevenLabs (para o "Só animação" e narração).

A chave fica SÓ no computador da pessoa, em ~/.corta/.env (permissão só do usuário), e é digitada
escondida pelo comando `corta chave elevenlabs` no Terminal — nunca vai num prompt nem na conversa.
Sem chave, o "Só animação" usa um áudio gravado pela própria pessoa.

A voz sai com o tempo de cada palavra (endpoint "with-timestamps"), para a legenda e o motion
acompanharem a fala.
"""
from __future__ import annotations

import base64
import getpass
import json
import os
import stat
import urllib.error
import urllib.request
from pathlib import Path

from .base import PASTA_USUARIO, CortaErro, log, salvar_json

ENV = PASTA_USUARIO / ".env"
API = "https://api.elevenlabs.io/v1"
MODELO_PADRAO = "eleven_multilingual_v2"


COMANDO_CHAVE = ("%USERPROFILE%\\.corta\\bin\\corta.cmd chave elevenlabs" if os.name == "nt"
                 else "~/.corta/bin/corta chave elevenlabs")


# ---------- chave ----------
def _ler_env() -> dict:
    if not ENV.exists():
        return {}
    out = {}
    for linha in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.strip().startswith("#"):
            k, v = linha.split("=", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def _gravar_env(dados: dict) -> None:
    PASTA_USUARIO.mkdir(parents=True, exist_ok=True)
    ENV.write_text("".join(f"{k}={v}\n" for k, v in dados.items()), encoding="utf-8")
    try:
        os.chmod(ENV, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def chave() -> str | None:
    return os.environ.get("ELEVENLABS_API_KEY") or _ler_env().get("ELEVENLABS_API_KEY")


def conectar(valor: str | None = None) -> None:
    if valor is None:
        log("Cole a sua chave da ElevenLabs (ela não aparece na tela) e aperte Enter:")
        valor = getpass.getpass("chave: ").strip()
    if len(valor) < 20:
        raise CortaErro("Essa chave parece incompleta. Copie de novo em elevenlabs.io → Profile → API Keys.")
    dados = _ler_env()
    dados["ELEVENLABS_API_KEY"] = valor
    _gravar_env(dados)
    try:
        n = len(vozes(silencioso=True))
        log(f"✅ ElevenLabs conectada ({n} vozes disponíveis). A chave ficou só neste computador: {ENV}")
    except CortaErro as e:
        log(f"⚠ A chave foi salva, mas a ElevenLabs recusou o teste: {e}")


def desconectar() -> None:
    dados = _ler_env()
    dados.pop("ELEVENLABS_API_KEY", None)
    _gravar_env(dados)
    log("ElevenLabs desconectada (chave apagada deste computador).")


def status() -> None:
    k = chave()
    log(f"ElevenLabs: {'conectada (…' + k[-4:] + ')' if k else f'não conectada — no Terminal: {COMANDO_CHAVE}'}")


# ---------- API ----------
def _pedir(caminho: str, corpo: dict | None = None) -> dict:
    k = chave()
    if not k:
        raise CortaErro(f"ElevenLabs não conectada. A pessoa roda no Terminal: {COMANDO_CHAVE} (ou use um áudio gravado dela).")
    req = urllib.request.Request(API + caminho, method="POST" if corpo is not None else "GET",
                                 headers={"xi-api-key": k, "Content-Type": "application/json", "Accept": "application/json"},
                                 data=json.dumps(corpo).encode() if corpo is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:300]
        if e.code == 401:
            raise CortaErro(f"A ElevenLabs recusou a chave (401). Conecte de novo no Terminal: {COMANDO_CHAVE}")
        if e.code in (402, 429):
            raise CortaErro(f"Sem créditos ou limite da ElevenLabs atingido ({e.code}). Veja o plano em elevenlabs.io.")
        raise CortaErro(f"ElevenLabs respondeu {e.code}: {msg}")
    except urllib.error.URLError as e:
        raise CortaErro(f"Sem conexão com a ElevenLabs: {e.reason}")


def vozes(silencioso: bool = False) -> list[dict]:
    js = _pedir("/voices")
    lista = [{"id": v["voice_id"], "nome": v.get("name", ""), "rotulos": v.get("labels", {}) or {}}
             for v in js.get("voices", [])]
    if not silencioso:
        for v in lista:
            r = v["rotulos"]
            log(f"{v['nome']:24s} {v['id']}  {r.get('gender', '')} {r.get('accent', '')} {r.get('description', '')}".rstrip())
    return lista


def palavras_do_alinhamento(alinh: dict) -> list[dict]:
    """Converte o alinhamento por letra da ElevenLabs em palavras com início e fim."""
    letras = alinh.get("characters", [])
    ini, fim = alinh.get("character_start_times_seconds", []), alinh.get("character_end_times_seconds", [])
    out, atual, t0, t1 = [], "", None, None
    for c, a, b in zip(letras, ini, fim):
        if c.isspace():
            if atual:
                out.append({"word": atual, "start": round(t0, 3), "end": round(t1, 3)})
            atual, t0 = "", None
            continue
        if t0 is None:
            t0 = a
        atual += c
        t1 = b
    if atual:
        out.append({"word": atual, "start": round(t0, 3), "end": round(t1, 3)})
    return out


def falar(texto: str, voz: str, destino: Path, modelo: str = MODELO_PADRAO, estabilidade: float = 0.45,
          semelhanca: float = 0.8, estilo: float = 0.15) -> tuple[Path, Path]:
    """Gera a narração (mp3) e as palavras com tempo (json, mesmo nome). `voz` = id ou nome da voz."""
    if len(texto) > 9000:
        raise CortaErro("Texto longo demais para uma narração só (máx. ~9 mil letras). Divida em partes.")
    vid = voz
    if not (len(voz) >= 18 and voz.isalnum()):
        achadas = [v for v in vozes(silencioso=True) if v["nome"].lower() == voz.lower()]
        if not achadas:
            raise CortaErro(f"Não achei a voz '{voz}'. Veja as vozes com: corta vozes")
        vid = achadas[0]["id"]
    js = _pedir(f"/text-to-speech/{vid}/with-timestamps?output_format=mp3_44100_128",
                {"text": texto, "model_id": modelo,
                 "voice_settings": {"stability": estabilidade, "similarity_boost": semelhanca, "style": estilo}})
    destino = Path(destino).with_suffix(".mp3")
    destino.write_bytes(base64.b64decode(js["audio_base64"]))
    palavras = palavras_do_alinhamento(js.get("normalized_alignment") or js.get("alignment") or {})
    arq_pal = destino.with_suffix(".json")
    salvar_json(arq_pal, palavras)
    log(f"   voz → {destino.name} ({len(palavras)} palavras com tempo em {arq_pal.name})")
    return destino, arq_pal
