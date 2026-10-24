"""Transcrição literal por palavra (mantém repetições e recomeços, que é onde estão os erros de fala).

Transcreve a voz limpa em blocos de ~30 s juntando os trechos de fala, ouvindo o ritmo real
(com as pausas), e descarta palavras fora dos trechos. Tempos no relógio do ORIGINAL.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import soundfile as sf

from .base import Cronometro, CortaErro, ler_json, log, pasta_job, salvar_json
from .perfil import carregar as carregar_perfil

PROMPT_LITERAL = {
    "pt": ("Transcrição literal, palavra por palavra, incluindo repetições, frases recomeçadas e erros: "
           "então, então eu vou, eu vou mostrar... mostrar pra você como funciona."),
    "en": "Verbatim transcript, word by word, including repetitions, restarts and mistakes: so, so I'm, I'm going to show... show you.",
    "es": "Transcripción literal, palabra por palabra, con repeticiones y frases reiniciadas: entonces, entonces yo, yo voy a mostrar...",
}

_modelos: dict = {}


# frases que o Whisper inventa em silêncio ou ruído (vistas nos testes de 23/10: aula de IA e IMG_0181)
INVENTADAS = {"obrigado", "obrigada", "ate mais", "ate a proxima", "tchau", "valeu", "obrigado por assistir",
              "legendas pela comunidade amaraorg", "inscrevase no canal", "thank you", "thanks for watching"}


def _normal(t: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFD", t.lower())
    return " ".join("".join(c for c in t if c.isalnum() or c == " ").split())


def _inventada(seg, audio: np.ndarray, b0: float, ref_rms: float, sr: int) -> bool:
    """Frase da lista que caiu num pedaço baixinho (menos de 1/4 do volume médio da fala) é invenção."""
    if _normal(seg.text) not in INVENTADAS:
        return False
    a, z = int((b0 + seg.start) * sr), int((b0 + seg.end) * sr)
    trecho = audio[a:z]
    if not len(trecho):
        return True
    return float(np.sqrt(np.mean(trecho ** 2))) < 0.25 * ref_rms or getattr(seg, "no_speech_prob", 0) > 0.5


def modelo(nome: str | None = None):
    from faster_whisper import WhisperModel
    p = carregar_perfil()["whisper"]
    nome = nome or os.environ.get("CORTA_MODELO") or p["modelo"]
    chave = (nome, p["device"], p["compute"])
    if chave not in _modelos:
        log(f"   carregando o modelo de transcrição {nome} (a 1ª vez baixa o modelo)…")
        _modelos[chave] = WhisperModel(nome, device=p["device"], compute_type=p["compute"])
    return _modelos[chave]


def audio16(voz: Path) -> np.ndarray:
    import scipy.signal as ss
    x, sr = sf.read(voz, dtype="float32", always_2d=True)
    return ss.resample_poly(x.mean(1), 16000, sr).astype(np.float32)


def transcrever_direto(video: Path, idioma: str = "pt") -> list[dict]:
    """Para legendar um vídeo que não passou pelas outras etapas: transcreve o áudio como está."""
    from .base import ffmpeg, rodar
    job = pasta_job(video.resolve())
    wav = job / "audio16.wav"
    rodar([ffmpeg(), "-y", "-v", "error", "-i", video, "-map", "0:a:0", "-ac", 1, "-ar", 16000, wav], descricao="extrair áudio")
    a, _ = sf.read(wav, dtype="float32")
    wav.unlink(missing_ok=True)
    c = Cronometro("transcrição")
    segs, _ = modelo().transcribe(a, language=idioma, word_timestamps=True, vad_filter=True, temperature=0)
    palavras = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
                for z in segs for w in (z.words or [])]
    c.fim()
    salvar_json(job / "palavras_direto.json", palavras)
    return palavras


def transcrever(video: Path, idioma: str = "pt", nome_modelo: str | None = None) -> list[dict]:
    from .base import saida_registrada
    _reg = saida_registrada(video.resolve())
    if _reg and _reg.get("palavras"):
        raise CortaErro(f"{video.name} já é um vídeo feito pelo Cortaí: não precisa preparar nem transcrever de novo. "
                        f"As palavras dele estão em: {_reg['palavras']} (use 'corta texto' para ler em frases).")
    job = pasta_job(video.resolve())
    if not (job / "trechos.json").exists():
        raise CortaErro("Rode primeiro: corta preparar <vídeo>")
    trechos = ler_json(job / "trechos.json")["trechos"]
    a = audio16(job / "voz.wav")
    m = modelo(nome_modelo)
    c = Cronometro("transcrição")
    # Áudio "condensado": só a fala, com as pausas encurtadas para 0,35 s. Com as pausas longas o Whisper
    # pulava a 1ª palavra curta depois delas ("Sabe", "Mas", "Clica", "tenta") e isso escondia recomeços
    # (teste real de 23/10). Os tempos voltam para o relógio do original.
    SR, BORDA, PAUSA = 16000, 0.15, 0.35
    pecas, mapa, t = [], [], 0.0
    for s0, e0 in trechos:
        s2, e2 = max(0.0, s0 - BORDA), e0 + BORDA
        seg = a[int(s2 * SR): int(e2 * SR)]
        mapa.append((t, s2, len(seg) / SR))
        pecas += [seg, np.zeros(int(PAUSA * SR), np.float32)]
        t += len(seg) / SR + PAUSA
    cond = np.concatenate(pecas) if pecas else np.zeros(1, np.float32)
    limites = [0.0]                       # blocos de ~25 s, sempre cortados entre trechos
    for c0, _, dur in mapa:
        if c0 + dur - limites[-1] > 25 and c0 > limites[-1]:
            limites.append(c0)
    limites.append(len(cond) / SR)
    brutas, inventadas = [], 0
    ref_rms = float(np.sqrt(np.mean(cond ** 2)) + 1e-9)
    for b0, b1 in zip(limites, limites[1:]):
        segs, _ = m.transcribe(cond[int(b0 * SR): int(b1 * SR)], language=idioma, word_timestamps=True, vad_filter=False,
                               condition_on_previous_text=False, initial_prompt=PROMPT_LITERAL.get(idioma), temperature=0)
        for z in segs:
            if _inventada(z, cond, b0, ref_rms, SR):
                inventadas += 1
                continue
            for w in z.words or []:
                tc = b0 + (w.start + w.end) / 2
                k = min(range(len(mapa)), key=lambda q: 0 if mapa[q][0] <= tc <= mapa[q][0] + mapa[q][2]
                        else min(abs(tc - mapa[q][0]), abs(tc - mapa[q][0] - mapa[q][2])))
                off = mapa[k][1] - mapa[k][0]
                brutas.append({"word": w.word.strip(), "start": b0 + w.start + off, "end": b0 + w.end + off})
        log(f"   {b1:.0f} s de {limites[-1]:.0f} s de fala")
    if inventadas:
        log(f"   {inventadas} frase(s) inventada(s) pelo Whisper em silêncio tirada(s) (\"Obrigado.\", \"Até a próxima!\"…)")
    # cada palavra vai para um trecho; a que cai numa pausa é do trecho SEGUINTE (fala não acontece na pausa)
    # e o tempo dela é preso dentro do trecho, para a legenda e a montagem não a perderem
    palavras = []
    for w in brutas:
        meio = (w["start"] + w["end"]) / 2
        k = next((q for q, (s0, e0) in enumerate(trechos) if s0 <= meio <= e0), None)
        if k is None:
            k = next((q for q, (s0, _) in enumerate(trechos) if meio < s0), len(trechos) - 1)
        s0, e0 = trechos[k]
        dur = max(0.05, min(w["end"] - w["start"], e0 - s0))
        ini = min(max(w["start"], s0), e0 - dur)
        palavras.append({"word": w["word"], "start": round(ini, 3), "end": round(min(e0, ini + dur), 3), "trecho": k})
    palavras.sort(key=lambda w: (w["trecho"], w["start"]))
    for x, y in zip(palavras, palavras[1:]):       # garante ordem sem sobreposição dentro do trecho
        if y["trecho"] == x["trecho"] and y["start"] < x["start"]:
            y["start"] = x["start"]
    c.fim()
    salvar_json(job / "palavras.json", palavras)
    log(f"   {len(palavras)} palavras → {job / 'palavras.json'}")
    return palavras
