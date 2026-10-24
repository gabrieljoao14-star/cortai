"""Trilha sonora ORIGINAL composta por código para cada vídeo, seguindo a edição.

Instrumentos do GeneralUser GS (licença permite uso comercial; arquivo no plugin) tocados pelo
tinysoundfont, que roda igual no Mac e no Windows (sem instalar nada além do plugin).

A trilha acompanha o vídeo:
- entra leve até o fim do gancho e então abre ("full");
- faz um vácuo de 0,35 s antes de cada virada e entra um acorde de impacto;
- no CTA resolve num acorde maior e segura até o fim, com fade.
Na mixagem ela fica bem abaixo da voz e abaixa sozinha quando a pessoa fala (ducking).

Estilos: emocional · corporativo · tensao · lofi · epico · energia.
"""
from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import soundfile as sf

from .base import RAIZ_PLUGIN, CortaErro, ffmpeg, log, rodar

SF2 = RAIZ_PLUGIN / "assets" / "musica" / "GeneralUser-GS.sf2"
SR = 48000
DRUMS = 9

# acorde = (baixo, notas do pad, notas do arpejo)
def _ac(baixo, pad, arp):
    return {"baixo": baixo, "pad": pad, "arp": arp}


ESTILOS = {
    "emocional": {  # piano e cordas, ré menor — a trilha dos criativos do Dr. Cláudio
        "bpm": 84, "prog": [_ac(38, [50, 53, 57, 64], [62, 65, 69, 72, 69, 65]), _ac(34, [50, 53, 57, 62], [58, 62, 65, 69, 65, 62]),
                            _ac(41, [48, 53, 57, 60], [60, 65, 69, 72, 69, 65]), _ac(36, [48, 52, 55, 62], [60, 64, 67, 72, 67, 64])],
        "cta": [_ac(34, [50, 53, 58, 62], [58, 62, 65, 70]), _ac(36, [48, 52, 55, 60], [60, 64, 67, 72]), _ac(41, [48, 53, 57, 60], [60, 65, 69, 72])],
        "inst": {"arp": 0, "pad": 49, "baixo": 43, "impacto": 47}, "bateria": None, "arp_div": 2,
        "descricao": "piano e cordas, sério e humano (depoimento, jurídico, saúde, histórias)"},
    "corporativo": {  # dó maior I–V–vi–IV, leve e otimista
        "bpm": 108, "prog": [_ac(36, [48, 52, 55, 60], [60, 64, 67, 72]), _ac(43, [47, 50, 55, 59], [59, 62, 67, 71]),
                             _ac(45, [48, 52, 57, 60], [57, 60, 64, 69]), _ac(41, [48, 53, 57, 60], [57, 60, 65, 69])],
        "cta": [_ac(41, [48, 53, 57, 60], [60, 65, 69, 72]), _ac(43, [47, 50, 55, 62], [62, 67, 71, 74]), _ac(36, [48, 52, 55, 60], [60, 64, 67, 72])],
        "inst": {"arp": 0, "pad": 89, "baixo": 33, "impacto": 47}, "bateria": "pop", "arp_div": 2,
        "descricao": "otimista e limpo (produto, empresa, tutorial, serviço)"},
    "tensao": {  # lá menor, cordas graves pulsando
        "bpm": 92, "prog": [_ac(33, [45, 48, 52, 57], [45, 45, 52, 45]), _ac(29, [41, 45, 48, 53], [41, 41, 48, 41]),
                            _ac(31, [43, 47, 50, 55], [43, 43, 50, 43]), _ac(28, [40, 44, 47, 52], [40, 40, 47, 40])],
        "cta": [_ac(29, [41, 45, 48, 53], [53, 57, 60]), _ac(31, [43, 47, 50, 55], [55, 59, 62]), _ac(33, [45, 49, 52, 57], [57, 61, 64])],
        "inst": {"arp": 48, "pad": 95, "baixo": 43, "impacto": 47}, "bateria": "pulso", "arp_div": 2,
        "descricao": "suspense e urgência (alerta, erro, prazo, golpe, polêmica)"},
    "lofi": {  # fá maior com sétimas, piano elétrico
        "bpm": 78, "prog": [_ac(41, [52, 57, 60, 64], [64, 69, 72, 76]), _ac(38, [48, 53, 57, 60], [60, 65, 69, 72]),
                            _ac(43, [50, 53, 57, 60], [62, 65, 69, 74]), _ac(36, [46, 52, 55, 58], [58, 64, 67, 70])],
        "cta": [_ac(38, [48, 53, 57, 60], [60, 65, 69]), _ac(43, [50, 53, 57, 60], [62, 65, 69]), _ac(41, [52, 57, 60, 64], [64, 69, 72])],
        "inst": {"arp": 4, "pad": 89, "baixo": 32, "impacto": 0}, "bateria": "lofi", "arp_div": 1,
        "descricao": "calmo e próximo (rotina, estudo, bastidor, lifestyle)"},
    "epico": {  # ré menor com metais e coro
        "bpm": 100, "prog": [_ac(38, [50, 53, 57, 62], [62, 65, 69]), _ac(34, [46, 50, 53, 58], [58, 62, 65]),
                             _ac(36, [48, 52, 55, 60], [60, 64, 67]), _ac(33, [45, 49, 52, 57], [57, 61, 64])],
        "cta": [_ac(34, [46, 50, 53, 58], [58, 62, 65]), _ac(36, [48, 52, 55, 60], [60, 64, 67]), _ac(38, [50, 54, 57, 62], [62, 66, 69])],
        "inst": {"arp": 61, "pad": 52, "baixo": 48, "impacto": 47}, "bateria": "epico", "arp_div": 1,
        "descricao": "grandioso (conquista, lançamento, transformação, antes e depois)"},
    "energia": {  # mi menor eletrônico, 4 no chão
        "bpm": 124, "prog": [_ac(40, [52, 55, 59, 64], [64, 67, 71, 76, 71, 67]), _ac(36, [48, 52, 55, 60], [60, 64, 67, 72, 67, 64]),
                             _ac(43, [50, 55, 59, 62], [62, 67, 71, 74, 71, 67]), _ac(38, [50, 54, 57, 62], [62, 66, 69, 74, 69, 66])],
        "cta": [_ac(36, [48, 52, 55, 60], [60, 64, 67, 72]), _ac(38, [50, 54, 57, 62], [62, 66, 69, 74]), _ac(40, [52, 56, 59, 64], [64, 68, 71, 76])],
        "inst": {"arp": 81, "pad": 90, "baixo": 38, "impacto": 47}, "bateria": "eletronica", "arp_div": 4,
        "descricao": "rápido e animado (fitness, vendas, dicas rápidas, tech)"},
}
CANAIS = {"arp": 0, "pad": 1, "baixo": 2, "impacto": 3}


def estilos() -> dict[str, str]:
    return {k: v["descricao"] for k, v in ESTILOS.items()}


def _bateria(tipo: str, t0: float, beat: float, compassos_fim: float, eventos: list, rng: random.Random):
    t = t0
    while t < compassos_fim:
        for k in range(8):                       # colcheias
            tt = t + k * beat / 2
            if tt >= compassos_fim:
                break
            swing = beat * 0.08 if (tipo == "lofi" and k % 2) else 0
            if tipo == "pop":
                if k in (0, 4): eventos.append((tt, DRUMS, 36, 0.2, 84))
                if k in (2, 6): eventos.append((tt, DRUMS, 39, 0.2, 70))
                eventos.append((tt, DRUMS, 42, 0.1, 44 + rng.randint(-6, 6)))
            elif tipo == "eletronica":
                if k % 2 == 0: eventos.append((tt, DRUMS, 36, 0.2, 96))
                if k in (2, 6): eventos.append((tt, DRUMS, 39, 0.2, 72))
                if k % 2 == 1: eventos.append((tt, DRUMS, 46, 0.1, 52))
            elif tipo == "lofi":
                if k in (0, 5): eventos.append((tt + swing, DRUMS, 36, 0.2, 70))
                if k in (2, 6): eventos.append((tt + swing, DRUMS, 37, 0.2, 58))
                eventos.append((tt + swing, DRUMS, 42, 0.1, 30 + rng.randint(-5, 5)))
            elif tipo == "pulso":
                if k == 0: eventos.append((tt, DRUMS, 35, 0.3, 80))
            elif tipo == "epico":
                if k in (0, 3, 4): eventos.append((tt, DRUMS, 36, 0.3, 100))
                if k == 6: eventos.append((tt, DRUMS, 49, 0.6, 60))
        t += beat * 4


def compor(estilo: str, duracao: float, gancho_ate: float = 0.0, impactos: list[float] | None = None,
           cta_em: float | None = None, semente: int = 11) -> np.ndarray:
    """Áudio estéreo float32 a 48 kHz, com a duração exata do vídeo."""
    import tinysoundfont
    if estilo not in ESTILOS:
        raise CortaErro(f"Trilha '{estilo}' não existe. Estilos: {', '.join(ESTILOS)}")
    if not SF2.exists():
        raise CortaErro("Instrumentos da trilha não encontrados no plugin. Atualize o plugin (claude plugin update cortai@cortai).")
    e, rng = ESTILOS[estilo], random.Random(semente)
    beat = 60 / e["bpm"]
    compasso = beat * 4
    impactos = sorted(impactos or [])
    cta = cta_em if cta_em is not None else duracao + 1
    eventos: list[tuple] = []   # (tempo, canal, nota, duração, força)

    def nota(ch, n, t0, t1, v):
        for h in impactos:                    # vácuo antes de cada impacto
            if h - 0.35 <= t0 < h:
                return
            if t0 < h - 0.35 < t1:
                t1 = h - 0.35
        if t1 > t0:
            eventos.append((max(0.0, t0 + (rng.uniform(-0.008, 0.008) if ch == CANAIS["arp"] else 0)), ch, n,
                            t1 - t0, max(1, min(127, int(v + rng.uniform(-5, 5))))))

    t, i = 0.0, 0
    while t < duracao:
        if t >= cta:
            ac = e["cta"][min(int((t - cta) // compasso), len(e["cta"]) - 1)]
        else:
            ac = e["prog"][i % len(e["prog"])]
        fim = min(t + compasso, duracao)
        ultimo = t >= cta and ac is e["cta"][-1]
        if ultimo:
            fim = duracao
        cheio = t + 0.01 >= gancho_ate
        for n in ac["pad"]:
            nota(CANAIS["pad"], n, t, fim + 0.05, 46 if cheio else 38)
        if cheio:
            nota(CANAIS["baixo"], ac["baixo"], t, fim, 60)
            passo = beat / e["arp_div"]
            k = 0
            while t + k * passo < fim and k < 4 * e["arp_div"]:
                tt = t + k * passo
                nota(CANAIS["arp"], ac["arp"][k % len(ac["arp"])], tt, tt + passo * 1.6, 50 if k % 2 == 0 else 40)
                k += 1
        else:
            nota(CANAIS["arp"], ac["arp"][0], t, t + beat * 2, 40)
        if ultimo:
            break
        t += compasso
        i += 1
    if e["bateria"]:
        ini = (int(gancho_ate // compasso) + (1 if gancho_ate % compasso else 0)) * compasso
        _bateria(e["bateria"], ini, beat, min(cta + compasso * 2, duracao), eventos, rng)
        eventos = [ev for ev in eventos if ev[1] != DRUMS or not any(h - 0.35 <= ev[0] < h for h in impactos)]
    for h in impactos:                         # impacto: grave forte + tímpano/prato
        ac = e["prog"][0]
        eventos.append((h, CANAIS["impacto"], 38, 2.0, 118))
        eventos.append((h, CANAIS["pad"], ac["pad"][0] + 12, 2.2, 72))
        eventos.append((h, CANAIS["baixo"], ac["baixo"], 2.4, 100))

    synth = tinysoundfont.Synth(samplerate=SR, gain=-6)
    sfid = synth.sfload(str(SF2))
    for nome, ch in CANAIS.items():
        synth.program_select(ch, sfid, 0, e["inst"][nome])
    synth.program_select(DRUMS, sfid, 128, 0, True)
    acoes = []
    for t0, ch, n, d, v in eventos:
        acoes.append((t0, 1, ch, n, v))
        acoes.append((t0 + d, 0, ch, n, 0))
    acoes.sort(key=lambda a: (a[0], a[1]))
    total = int((duracao + 0.5) * SR)
    saida = np.zeros((total, 2), np.float32)
    pos = 0
    for t0, liga, ch, n, v in acoes:
        alvo = min(total, int(t0 * SR))
        if alvo > pos:
            bloco = np.frombuffer(synth.generate(alvo - pos), dtype=np.float32).reshape(-1, 2)
            saida[pos: pos + len(bloco)] = bloco
            pos = alvo
        if liga:
            synth.noteon(ch, n, v)
        else:
            synth.noteoff(ch, n)
    if pos < total:
        bloco = np.frombuffer(synth.generate(total - pos), dtype=np.float32).reshape(-1, 2)
        saida[pos: pos + len(bloco)] = bloco
    saida = saida[: int(duracao * SR)]
    fade = min(len(saida), int(1.5 * SR))
    saida[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]
    return saida


def gerar(estilo: str, duracao: float, destino: Path, **kw) -> Path:
    """Compõe e grava em -20 LUFS (o nível final é ajustado na mixagem, bem abaixo da voz)."""
    bruto = destino.with_name(destino.stem + "_bruto.wav")
    sf.write(bruto, compor(estilo, duracao, **kw), SR, subtype="FLOAT")
    rodar([ffmpeg(), "-y", "-v", "error", "-i", bruto, "-af", "loudnorm=I=-20:TP=-2:LRA=11", "-ar", SR, "-ac", 2, destino],
          descricao="volume da trilha")
    bruto.unlink(missing_ok=True)
    log(f"   trilha '{estilo}' ({duracao:.1f} s) → {destino.name}")
    return destino


def preparar_arquivo(arquivo: Path, duracao: float, destino: Path) -> Path:
    """Música da própria pessoa: repete se for curta, corta na duração e faz fade no fim."""
    if not arquivo.exists():
        raise CortaErro(f"Não achei a música {arquivo}")
    rodar([ffmpeg(), "-y", "-v", "error", "-stream_loop", -1, "-i", arquivo, "-t", f"{duracao:.3f}",
           "-af", f"afade=t=out:st={max(0, duracao - 1.5):.3f}:d=1.5,loudnorm=I=-20:TP=-2:LRA=11",
           "-ar", SR, "-ac", 2, destino], descricao="preparar a música")
    return destino
