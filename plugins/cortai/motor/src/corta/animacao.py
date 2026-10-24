"""Só animação: vídeo inteiro de motion (Remotion), sem gravação de pessoa, no tempo da narração.

1. `corta narracao` — voz da ElevenLabs (texto + voz) ou áudio gravado pela pessoa; sai a narração e as
   palavras com tempo.
2. O Claude escreve cenas.json ancorando cada cena nas palavras (algo novo a cada 2–4 s).
3. `corta animacao` — grava as cenas no Remotion, junta a narração e registra as palavras: depois é só
   `corta legendar` (legenda, trilha, sons) e `corta quadros` para o ciclo de crítica.

cenas.json:
  {"destaque": "#FFE14D", "cenas": [{"tipo": "titulo", "inicio": 0, "fim": 3,
                                      "props": {"texto": "Você está perdendo dinheiro", "chave": "dinheiro"}}, …]}
Tipos: titulo, frase, palavra-gigante, lista, contador, grafico, manchetes, nome-cargo, emoji, imagem ("arquivo").
Nas cenas com texto a legenda some sozinha; `"legenda": true|false` na cena muda isso.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .base import (CortaErro, ffmpeg, info_video, ler_json, log, pasta_job, registrar_saida, rodar, saida_livre,
                   salvar_json)
from .efeitos import MOTION, _npx

# cenas cujo texto já é a narração: a legenda some de baixo nelas (sem texto duplicado na tela)
TEXTO_NA_CENA = {"titulo", "frase", "palavra-gigante", "lista", "manchetes", "contador", "grafico"}
FORMATOS = {"9:16": (1080, 1920), "4:5": (1080, 1350), "1:1": (1080, 1080), "16:9": (1920, 1080)}


def narracao(saida: Path, texto: str | None = None, voz: str | None = None, audio: Path | None = None,
             idioma: str = "pt") -> tuple[Path, Path]:
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    if audio:
        audio = Path(audio).resolve()
        if not audio.exists():
            raise CortaErro(f"Não achei o áudio {audio}")
        destino = saida.with_suffix(".wav")
        rodar([ffmpeg(), "-y", "-v", "error", "-i", audio, "-af", "highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11",
               "-ar", 48000, "-ac", 2, destino], descricao="preparar a narração")
        from .transcrever import modelo
        import soundfile as sf
        import numpy as np
        import scipy.signal as ss
        x, sr = sf.read(destino, dtype="float32", always_2d=True)
        a16 = ss.resample_poly(x.mean(1), 16000, sr).astype(np.float32)
        segs, _ = modelo().transcribe(a16, language=idioma, word_timestamps=True, vad_filter=True, temperature=0)
        palavras = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
                    for z in segs for w in (z.words or [])]
        arq = saida.with_suffix(".json")
        salvar_json(arq, palavras)
        log(f"   narração própria → {destino.name} ({len(palavras)} palavras com tempo)")
        return destino, arq
    if not (texto and voz):
        raise CortaErro("Diga o roteiro e a voz (ElevenLabs), ou passe um áudio gravado (--audio).")
    from .voz import falar
    return falar(texto, voz, saida)


def animacao(cenas: Path, narr: Path, palavras: Path | None, saida: Path, formato: str = "9:16") -> Path:
    if formato not in FORMATOS:
        raise CortaErro(f"Formato '{formato}' não existe. Use: {', '.join(FORMATOS)}")
    narr, cenas = Path(narr).resolve(), Path(cenas).resolve()
    dados = ler_json(cenas)
    if not dados.get("cenas"):
        raise CortaErro("cenas.json sem cenas.")
    dur = info_video_audio(narr) + 0.6
    fim_cenas = max(c["fim"] for c in dados["cenas"])
    if fim_cenas < dur - 1.0:
        log(f"   ⚠ as cenas acabam em {fim_cenas:.1f} s e a narração vai até {dur:.1f} s: o fim fica só com o fundo")
    W, H = FORMATOS[formato]
    from .efeitos import embutir_imagem
    for c in dados["cenas"]:
        if c["tipo"] == "imagem":
            c["props"] = embutir_imagem(c.get("props") or {}, W, H, cenas.parent)
    saida = saida_livre(Path(saida).resolve())
    job = pasta_job(saida)
    props = {**dados, "tipo": "animacao", "largura": W, "altura": H, "fps": 30, "duracao": round(dur, 3)}
    arq_props = job / "animacao_props.json"
    salvar_json(arq_props, props)
    mudo = job / "animacao_muda.mp4"
    npx = _npx()
    ambiente = dict(os.environ)
    ambiente["PATH"] = str(Path(npx).parent) + os.pathsep + ambiente.get("PATH", "")
    log(f"== animação {len(dados['cenas'])} cenas · {dur:.1f} s · {W}x{H}")
    r = subprocess.run([npx, "remotion", "render", "src/index.ts", "Animacao", str(mudo), f"--props={arq_props}",
                        "--codec=h264", "--crf=17", "--log=error"], cwd=str(MOTION), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ambiente)
    if r.returncode != 0 or not mudo.exists():
        raise CortaErro("A animação não renderizou.\n" + (r.stderr or r.stdout)[-1500:])
    # a narração ganha silêncio no fim: a última cena termina de sair antes do vídeo acabar
    rodar([ffmpeg(), "-y", "-v", "error", "-i", mudo, "-i", narr, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
           "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", "-movflags", "+faststart", saida],
          descricao="juntar a narração")
    mudo.unlink(missing_ok=True)
    item = {"arquivo": str(saida), "etapa": "animacao",
            "sem_legenda": [[c["inicio"], c["fim"]] for c in dados["cenas"]
                            if c.get("legenda") is not True and (c["tipo"] in TEXTO_NA_CENA or c.get("legenda") is False)]}
    if palavras and Path(palavras).exists():
        destino_pal = job / "palavras_animacao.json"
        shutil.copy2(palavras, destino_pal)
        item["palavras"] = str(destino_pal)
    registrar_saida(job, item)
    log(f"   → {saida}")
    log("   próximo: corta legendar (legenda, trilha, sons) e corta quadros para a crítica")
    return saida


def info_video_audio(arq: Path) -> float:
    from .base import ffprobe
    r = rodar([ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq])
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise CortaErro(f"Não consegui ler a duração de {arq.name}")
