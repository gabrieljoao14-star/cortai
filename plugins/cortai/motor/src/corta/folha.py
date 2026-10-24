"""Folha de quadros do vídeo pronto: o Claude abre a imagem e confere gancho, legenda e CTA antes de
entregar (e no ciclo de crítica dos vídeos com motion). Cada quadro sai com o segundo escrito embaixo."""
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from .base import CortaErro, ffmpeg, info_video, ler_json, log, nome_seguro, pasta_job, saida_registrada


def _momentos(video: Path, dur: float, n: int) -> list[float]:
    tempos = []
    reg = saida_registrada(video) or {}
    if reg.get("blocos") and Path(reg["blocos"]).exists():
        b = ler_json(reg["blocos"])
        if b.get("gancho"):
            tempos += [0.4, max(0.5, (b.get("gancho_ate") or 3.5) - 0.6)]
        if b.get("cta") and b.get("cta_em") is not None:
            tempos.append(min(dur - 0.2, b["cta_em"] + 0.8))
    resto = max(0, n - len(tempos))
    tempos += [dur * (k + 1) / (resto + 1) for k in range(resto)]
    return sorted({round(t, 2) for t in tempos if 0 <= t < dur})


def quadros(video: Path, em: list[float] | None = None, n: int = 8) -> Path:
    video = video.resolve()
    if not video.exists():
        raise CortaErro(f"Não achei {video}")
    info = info_video(video)
    tempos = sorted(em) if em else _momentos(video, info["duracao"], n)
    vertical = info["altura"] > info["largura"]
    w = 300 if vertical else 480
    h = int(w * info["altura"] / info["largura"])
    cols = min(len(tempos), 4 if vertical else 3)
    linhas = (len(tempos) + cols - 1) // cols
    folha = Image.new("RGB", (cols * (w + 10) + 10, linhas * (h + 40) + 10), (24, 24, 28))
    d = ImageDraw.Draw(folha)
    for i, t in enumerate(tempos):
        png = subprocess.run([ffmpeg(), "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                              "-vf", f"scale={w}:{h}", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        if not png:
            log(f"   ⚠ não consegui tirar o quadro de {t:.1f} s (depois do fim do vídeo?)")
            continue
        import io
        q = Image.open(io.BytesIO(png)).convert("RGB")
        x, y = 10 + (i % cols) * (w + 10), 10 + (i // cols) * (h + 40)
        folha.paste(q, (x, y))
        d.text((x + 4, y + h + 8), f"{int(t // 60)}:{t % 60:05.2f}", fill=(230, 230, 230))
    reg = saida_registrada(video)
    pasta = Path(reg["job"]) if reg and reg.get("job") else pasta_job(video)
    destino = pasta / f"quadros_{nome_seguro(video.stem)}.png"
    folha.save(destino)
    log(f"   {len(tempos)} quadros ({', '.join(f'{t:.1f}s' for t in tempos)}) → {destino}")
    log("   abra a imagem e confira: gancho legível e fora do rosto, legenda sem palavra cortada, CTA certo")
    return destino
