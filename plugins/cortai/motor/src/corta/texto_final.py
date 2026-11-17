"""Ouve o vídeo final inteiro e compara com o texto que devia estar nele.

A conferência antiga media duração, som e imagem, mas não lia o resultado: resto de take, palavra
engolida na emenda e fala de bastidor passavam (13/11). Aqui o áudio do ARQUIVO FINAL é transcrito
de novo, em janelas de ~30 s cortadas em pausas, e o texto ouvido é comparado com as palavras da
edição. Sai:

- sobras: o que se ouve e não está no texto (resto de take, bastidor, começo da palavra seguinte);
- faltas: o que está no texto e não se ouve (palavra engolida na emenda);
- trocas: palavra diferente bem em cima de uma emenda (palavra cortada pela metade soa como outra);
- repetidas: a mesma sequência dita duas vezes seguidas ou quase (recomeço que ficou).

Diferença de grafia ("holerite" × "lerite", "97" × "noventa e sete") não é aviso: a legenda usa o
texto corrigido pela pessoa, não o que o Whisper ouviu agora.
"""
from __future__ import annotations

import difflib
import re

import numpy as np

SR = 16000
JANELA = 30.0           # tamanho de cada janela de transcrição
BUSCA = 3.0             # a borda da janela procura a pausa mais quieta até 3 s para cada lado
PERTO_EMENDA = 0.4      # diferença a menos disso de um corte conta como "na emenda"
REPETE_ATE = 20.0       # a mesma sequência de novo em até 20 s é suspeita de recomeço


def norm(p: str) -> str:
    return re.sub(r"[^\wà-ú]", "", p.lower())


def janelas(x: np.ndarray, alvo: float = JANELA, busca: float = BUSCA) -> list[tuple[float, float]]:
    """Divide o áudio em janelas de ~`alvo` s, cortando sempre no ponto mais quieto perto da borda."""
    dur = len(x) / SR
    if dur <= alvo + busca:
        return [(0.0, dur)]
    n = 320                                                    # 20 ms
    k = len(x) // n
    db = 20 * np.log10(np.sqrt((x[: k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)
    suave = np.convolve(db, np.ones(10) / 10, mode="same")     # média de 0,2 s
    cortes, t = [0.0], alvo
    while t < dur - busca:
        a, b = int((t - busca) / 0.02), min(k, int((t + busca) / 0.02))
        c = (a + int(np.argmin(suave[a:b]))) * 0.02
        cortes.append(c)
        t = c + alvo
    cortes.append(dur)
    return [(a, b) for a, b in zip(cortes, cortes[1:]) if b - a > 0.2]


def ouvir(x: np.ndarray, idioma: str = "pt", avisar=None) -> list[dict]:
    """Transcreve o áudio final inteiro, janela por janela. Tempos no relógio do vídeo final."""
    from .transcrever import PROMPT_LITERAL, modelo
    m = modelo()
    partes = janelas(x)
    palavras = []
    for q, (a, b) in enumerate(partes, 1):
        segs, _ = m.transcribe(x[int(a * SR): int(b * SR)], language=idioma, word_timestamps=True, vad_filter=False,
                               condition_on_previous_text=False, initial_prompt=PROMPT_LITERAL.get(idioma), temperature=0)
        for z in segs:
            if getattr(z, "no_speech_prob", 0) > 0.8:
                continue
            for w in z.words or []:
                if w.word.strip():
                    palavras.append({"word": w.word.strip(), "start": round(a + w.start, 3), "end": round(a + w.end, 3),
                                     "janela": q - 1})
        if avisar and len(partes) > 1:
            avisar(q, len(partes), b)
    return palavras


def _trecho(ws: list[dict]) -> dict:
    return {"em": round(ws[0]["start"], 2), "ate": round(ws[-1]["end"], 2), "texto": " ".join(w["word"] for w in ws)}


def _parecidas(a: list[str], b: list[str]) -> bool:
    ja, jb = "".join(a), "".join(b)
    if any(c.isdigit() for c in ja + jb):          # número por extenso × em algarismo
        return True
    return difflib.SequenceMatcher(None, ja, jb, autojunk=False).ratio() >= 0.6


def repetidas(ouvidas: list[dict], ate: float = REPETE_ATE) -> list[dict]:
    """Sequências ditas duas vezes: 4+ palavras de novo em até `ate` s, ou 3+ logo em seguida."""
    ws = [w for w in ouvidas if norm(w["word"])]
    t = [norm(w["word"]) for w in ws]
    achados, usado = [], set()
    i = 0
    while i < len(t):
        melhor = None
        j = i + 2
        while j < len(t) and ws[j]["start"] - ws[i]["start"] <= ate:
            n = 0
            while i + n < j and j + n < len(t) and t[i + n] == t[j + n]:
                n += 1
            colado = j - (i + n) <= 2                 # a 2ª vez começa logo depois da 1ª: recomeço típico
            if (n >= 4 or (n >= 3 and colado)) and sum(len(p) for p in t[i: i + n]) >= 8 and j not in usado:
                if melhor is None or n > melhor[1]:
                    melhor = (j, n)
            j += 1
        if melhor:
            j, n = melhor
            usado.update(range(j, j + n))
            achados.append({**_trecho(ws[i: i + n]), "de_novo_em": round(ws[j]["start"], 2)})
            i += n
        else:
            i += 1
    return achados


def comparar(esperadas: list[dict], ouvidas: list[dict], emendas: list[float] | None = None) -> dict:
    """Compara o texto da edição com o que se ouve no arquivo final."""
    emendas = emendas or []
    E = [w for w in esperadas if norm(w["word"])]
    O = [w for w in ouvidas if norm(w["word"])]
    a, b = [norm(w["word"]) for w in E], [norm(w["word"]) for w in O]

    def na_emenda(t0: float, t1: float) -> bool:
        return any(t0 - PERTO_EMENDA <= c <= t1 + PERTO_EMENDA for c in emendas)

    def tempo_esperado(i: int) -> float:
        # onde, no vídeo final, cairia a palavra esperada número i
        return E[min(i, len(E) - 1)]["start"] if E else 0.0

    sobras, faltas, trocas, iguais = [], [], [], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        ne, no = i2 - i1, j2 - j1
        if op == "equal":
            iguais += ne
        elif op == "insert":
            perto = na_emenda(O[j1]["start"], O[j2 - 1]["end"])
            if no >= 2 or perto:
                sobras.append({**_trecho(O[j1:j2]), "emenda": perto})
        elif op == "delete":
            perto = na_emenda(E[i1]["start"], E[i2 - 1]["end"])
            if ne >= 2 or perto:
                faltas.append({**_trecho(E[i1:i2]), "emenda": perto})
        else:
            perto = na_emenda(O[j1]["start"], O[j2 - 1]["end"])
            if _parecidas(a[i1:i2], b[j1:j2]):
                continue
            if no - ne >= 2:
                sobras.append({**_trecho(O[j1:j2]), "emenda": perto, "no_lugar_de": " ".join(w["word"] for w in E[i1:i2])})
            elif ne - no >= 2:
                faltas.append({**_trecho(E[i1:i2]), "emenda": perto, "ouvido": " ".join(w["word"] for w in O[j1:j2])})
            elif perto:
                trocas.append({**_trecho(O[j1:j2]), "esperado": " ".join(w["word"] for w in E[i1:i2])})
    return {"palavras_esperadas": len(a), "palavras_ouvidas": len(b), "iguais": iguais,
            "sobras": sobras, "faltas": faltas, "trocas": trocas, "repetidas": repetidas(O)}


def em_linhas(ouvidas: list[dict]) -> list[str]:
    """O texto ouvido, uma linha por janela, com o minuto: é para ler inteiro antes de entregar."""
    linhas, atual, q = [], [], None
    for w in ouvidas:
        if q is not None and w.get("janela") != q and atual:
            linhas.append(atual)
            atual = []
        q = w.get("janela")
        atual.append(w)
    if atual:
        linhas.append(atual)
    return [f"{int(l[0]['start'] // 60)}:{int(l[0]['start'] % 60):02d}  {' '.join(w['word'] for w in l)}" for l in linhas]
