"""Peças comuns: achar ffmpeg, rodar comandos, ler o vídeo, pasta de trabalho, JSON.

Regras que valem para o motor inteiro (vieram das lições das notas 01–04):
- nunca sobrescrever o original nem uma saída anterior (`saida_livre`);
- caminhos sempre como lista de argumentos, nunca string de shell (acentos e espaços no Windows);
- texto em UTF-8 de ponta a ponta.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAIZ_PLUGIN = Path(os.environ.get("CORTA_RAIZ") or Path(__file__).resolve().parents[3])
PASTA_USUARIO = Path(os.environ.get("CORTA_HOME") or (Path.home() / ".corta"))
EXE = ".exe" if os.name == "nt" else ""


class CortaErro(Exception):
    """Erro com mensagem para a pessoa (em português simples, com o que fazer)."""


def log(msg: str) -> None:
    print(msg, flush=True)


def achar_bin(nome: str) -> str:
    env = os.environ.get(f"CORTA_{nome.upper()}")
    if env and Path(env).exists():
        return env
    local = PASTA_USUARIO / "bin" / f"{nome}{EXE}"
    if local.exists():
        return str(local)
    achado = shutil.which(nome)
    if achado:
        return achado
    raise CortaErro(f"Não achei o {nome}. Rode a instalação de novo: /cortai:instalar")


def ffmpeg() -> str:
    return achar_bin("ffmpeg")


def ffprobe() -> str:
    return achar_bin("ffprobe")


def _descendentes(pid: int) -> list[int]:
    """Processos abertos por `pid` (filhos, netos…), lidos do `ps` (Mac e Linux)."""
    try:
        linhas = subprocess.run(["ps", "-A", "-o", "pid=,ppid="], capture_output=True, text=True, timeout=5).stdout.split("\n")
    except Exception:
        return []
    pais: dict[int, list[int]] = {}
    for ln in linhas:
        partes = ln.split()
        if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
            pais.setdefault(int(partes[1]), []).append(int(partes[0]))
    out, fila = [], [pid]
    while fila:
        for f in pais.get(fila.pop(), []):
            out.append(f)
            fila.append(f)
    return out


def encerrar_filhos() -> None:
    """Fecha o ffmpeg, o detector de rosto e o Remotion que este comando abriu. Sem isso, quem interrompe
    o motor deixa um ffmpeg rodando sozinho (achado no teste da aula de 1h31, 23/10)."""
    import signal
    if os.name == "nt":
        filhos = subprocess.run(["powershell", "-NoProfile", "-Command",
                                 f"(Get-CimInstance Win32_Process -Filter 'ParentProcessId={os.getpid()}').ProcessId"],
                                capture_output=True, text=True).stdout.split()
        for f in filhos:
            if f.isdigit():
                subprocess.run(["taskkill", "/F", "/T", "/PID", f], capture_output=True)
        return
    for f in reversed(_descendentes(os.getpid())):
        try:
            os.kill(f, signal.SIGKILL)
        except OSError:
            pass


def supervisionar(argv: list[str]) -> int | None:
    """Mac e Linux: o comando vira um supervisor leve e o trabalho roda num processo filho. Quem para a
    conversa manda SIGTERM; o supervisor está só esperando, responde na hora e fecha a árvore inteira
    (trabalho + ffmpeg + detector). O trabalho sozinho não responderia: com o Whisper rodando em C, o Python
    só trata o sinal quando a chamada termina (teste de 23/10). Devolve o código de saída, ou None se este
    processo já é o trabalhador (ou no Windows)."""
    import signal
    if os.name == "nt" or os.environ.get("CORTA_TRABALHADOR") == "1":
        return None
    amb = dict(os.environ, CORTA_TRABALHADOR="1")
    filho = subprocess.Popen([sys.executable, "-c", "import sys; from corta.cli import main; main(sys.argv[1:])", *argv],
                             env=amb)

    def sair(sig, _quadro):
        encerrar_filhos()
        os._exit(128 + sig)
    for nome in ("SIGTERM", "SIGHUP", "SIGINT"):
        if hasattr(signal, nome):
            signal.signal(getattr(signal, nome), sair)
    return filho.wait()


def proteger_filhos() -> None:
    """Conversa parada ou terminal fechado: fecha os processos filhos antes de sair (o Ctrl+C é tratado no cli)."""
    import signal

    def sair(sig, _quadro):
        encerrar_filhos()
        os._exit(128 + sig)
    for nome in ("SIGTERM", "SIGHUP"):
        if hasattr(signal, nome):
            signal.signal(getattr(signal, nome), sair)


def rodar(cmd: list, *, descricao: str = "") -> subprocess.CompletedProcess:
    cmd = [str(c) for c in cmd]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        nome = descricao or Path(cmd[0]).name
        raise CortaErro(f"Falhou: {nome}\n{r.stderr[-2000:]}")
    return r


def info_video(caminho: Path) -> dict:
    r = rodar([ffprobe(), "-v", "error", "-show_streams", "-show_format", "-of", "json", caminho], descricao="ffprobe")
    js = json.loads(r.stdout)
    v = next((s for s in js["streams"] if s.get("codec_type") == "video"), None)
    a = next((s for s in js["streams"] if s.get("codec_type") == "audio"), None)
    if v is None:
        raise CortaErro(f"{caminho.name} não tem imagem de vídeo.")
    w, h = int(v["width"]), int(v["height"])
    # vídeo do celular gravado "deitado": o ffmpeg gira sozinho ao decodificar, então troca largura/altura
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    if "rotate" in (v.get("tags") or {}):
        rot = int(v["tags"]["rotate"])
    if abs(rot) % 180 == 90:
        w, h = h, w
    num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    dur = float(js["format"].get("duration") or v.get("duration") or 0)
    return {"largura": w, "altura": h, "fps": fps, "duracao": dur, "tem_audio": a is not None}


def fps_saida(fps: float) -> int:
    """Quadro inteiro e que divide 48 kHz (cada quadro = N amostras exatas): 29,97 → 30, 23,976 → 24."""
    f = int(round(fps)) or 30
    f = min(f, 60)
    return f if 48000 % f == 0 else 30


def nome_seguro(texto: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", texto).strip() or "video"


def pasta_job(video: Path) -> Path:
    p = video.parent / "_corta" / nome_seguro(video.stem)
    p.mkdir(parents=True, exist_ok=True)
    return p


def saida_livre(desejada: Path) -> Path:
    """Nunca sobrescreve: se o arquivo existe, vira 'nome (2).mp4', 'nome (3).mp4'…"""
    if not desejada.exists():
        return desejada
    i = 2
    while True:
        c = desejada.with_name(f"{desejada.stem} ({i}){desejada.suffix}")
        if not c.exists():
            return c
        i += 1


def ler_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def salvar_json(p: Path, dados) -> None:
    Path(p).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


def conferir_arquivo_local(video: Path) -> None:
    """OneDrive/iCloud podem deixar o arquivo 'só na nuvem': existe na pasta mas não tem os dados."""
    if not video.exists():
        raise CortaErro(f"Não achei o arquivo: {video}")
    try:
        with open(video, "rb") as f:
            f.read(1024)
    except OSError as e:
        raise CortaErro(f"Não consegui ler {video.name}. Se ele está no OneDrive ou iCloud, baixe para o computador primeiro. ({e})")
    if video.stat().st_size < 1024:
        raise CortaErro(f"{video.name} parece vazio ou só na nuvem. Baixe o arquivo para o computador e tente de novo.")


class Cronometro:
    def __init__(self, nome: str):
        self.nome, self.t0 = nome, time.time()

    def fim(self) -> float:
        s = time.time() - self.t0
        log(f"   ({self.nome}: {s / 60:.1f} min)" if s >= 60 else f"   ({self.nome}: {s:.0f} s)")
        return s


def configurar_saida_utf8() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


def registrar_saida(job: Path, item: dict) -> None:
    """Anota a saída no job e num índice global (~/.corta/saidas.json): assim a legenda acha as
    palavras certas mesmo se o vídeo editado for movido para outra pasta... desde que o caminho não mude."""
    reg = job / "saidas.json"
    lista = ler_json(reg) if reg.exists() else []
    lista.append(item)
    salvar_json(reg, lista)
    glob_ = PASTA_USUARIO / "saidas.json"
    PASTA_USUARIO.mkdir(parents=True, exist_ok=True)
    try:
        indice = ler_json(glob_) if glob_.exists() else {}
    except ValueError:
        indice = {}
    indice[item["arquivo"]] = {**item, "job": str(job)}
    salvar_json(glob_, indice)


def saida_registrada(arquivo: Path) -> dict | None:
    glob_ = PASTA_USUARIO / "saidas.json"
    if not glob_.exists():
        return None
    try:
        return ler_json(glob_).get(str(Path(arquivo).resolve()))
    except ValueError:
        return None


def manter_acordado() -> None:
    """Edição longa não pode parar porque o computador dormiu (lição das notas: Mac dormindo trava o job)."""
    try:
        if sys.platform == "darwin" and shutil.which("caffeinate"):
            subprocess.Popen(["caffeinate", "-dimsu", "-w", str(os.getpid())],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif os.name == "nt":
            import ctypes
            # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED: vale enquanto este processo existir
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000040)
    except Exception:
        pass
