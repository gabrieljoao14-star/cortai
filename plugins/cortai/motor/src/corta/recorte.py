"""Recorte da pessoa (MODNet, licença Apache 2.0, roda no onnxruntime que o motor já tem; igual no
Mac — inclusive Intel — e no Windows). Gera um vídeo com transparência só com a pessoa, para colocar
POR CIMA de um efeito: a palavra gigante fica "atrás" de quem fala.

Cada quadro passa pelo modelo a 512 px de altura; a máscara é suavizada no tempo (sem tremer) e nas
bordas (sem serrilhado).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from .base import RAIZ_PLUGIN, CortaErro, ffmpeg, info_video

MODELO = RAIZ_PLUGIN / "assets" / "modelos" / "modnet.onnx"
_sessao = None


def _modelo():
    global _sessao
    if _sessao is None:
        import onnxruntime as ort
        if not MODELO.exists():
            raise CortaErro("Modelo de recorte não encontrado no plugin. Atualize o plugin (claude plugin update cortai@cortai).")
        _sessao = ort.InferenceSession(str(MODELO), providers=["CPUExecutionProvider"])
    return _sessao


def mascara(quadro: np.ndarray) -> np.ndarray:
    """Alfa 0..1 (float32) do tamanho do quadro RGB."""
    s = _modelo()
    H, W = quadro.shape[:2]
    h = 512
    w = max(32, int(round(W * h / H / 32)) * 32)
    x = (np.asarray(Image.fromarray(quadro).resize((w, h), Image.BILINEAR), dtype=np.float32) / 255 - 0.5) / 0.5
    m = s.run(None, {s.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0][0, 0]
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), dtype=np.float32) / 255


def recortar(video: Path, ini: float, dur: float, fps: int, destino: Path) -> Path:
    """Vídeo (ProRes 4444 com alfa) só com a pessoa, de `ini` até `ini + dur` do vídeo."""
    if destino.exists():
        return destino
    info = info_video(video)
    W, H = info["largura"], info["altura"]
    ler = subprocess.Popen([ffmpeg(), "-v", "error", "-ss", f"{ini:.3f}", "-t", f"{dur:.3f}", "-i", str(video),
                            "-vf", f"fps={fps}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    gravar = subprocess.Popen([ffmpeg(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                               "-r", str(fps), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                               str(destino)], stdin=subprocess.PIPE)
    tam, anterior = W * H * 3, None
    borda = ImageFilter.GaussianBlur(radius=max(1, W // 540))
    while True:
        buf = ler.stdout.read(tam)
        if len(buf) < tam:
            break
        q = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        a = mascara(q)
        if anterior is not None:
            a = 0.65 * a + 0.35 * anterior        # suaviza no tempo: a borda não "ferve"
        anterior = a
        alfa = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(borda))
        gravar.stdin.write(np.dstack([q, alfa]).tobytes())
    ler.wait()
    gravar.stdin.close()
    gravar.wait()
    if gravar.returncode != 0 or not destino.exists():
        raise CortaErro("O recorte da pessoa falhou ao gravar.")
    return destino
