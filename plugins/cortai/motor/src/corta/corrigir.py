"""Corrige palavras que o Whisper errou ("lerite" → "holerite", "Cloud" → "Claude").

Corrige só as palavras do vídeo indicado: um vídeo feito pelo Cortaí mexe só nas palavras dele (o
original fica intacto para ajustes e cortes futuros); o vídeo original mexe só no `palavras.json`.
Regras (achadas no teste real de 23/10):
- a pontuação colada na palavra é ignorada na busca e preservada no resultado ("aqui," acha "aqui,");
- "errado=certo" com mais palavras do lado certo cria palavras separadas, dividindo o tempo
  ("aquele aposentado=Sabe aquele aposentado" → 3 palavras, cada uma com seu destaque);
- `--em SEGUNDOS` troca só a ocorrência mais perto desse tempo (padrão: todas);
- correção que começa com "-" funciona (ex.: "-fé=fé").
"""
from __future__ import annotations

import re
from pathlib import Path

from .base import CortaErro, ler_json, log, pasta_job, saida_registrada, salvar_json

PONTA = ".,;:!?…\"“”()"
_RE = re.compile(rf"^([{re.escape(PONTA)}]*)(.*?)([{re.escape(PONTA)}]*)$")


def _separa(t: str):
    m = _RE.match(t.strip())
    return m.group(1), m.group(2), m.group(3)


def _miolo(t: str) -> str:
    return _separa(t)[1].lower()


def _aplicar(palavras: list[dict], errado: list[str], certo: list[str], em: float | None) -> tuple[list[dict], int]:
    n = len(errado)
    alvo = [_miolo(e) for e in errado]
    achados = [i for i in range(len(palavras) - n + 1) if [_miolo(w["word"]) for w in palavras[i: i + n]] == alvo]
    if em is not None and achados:
        achados = [min(achados, key=lambda i: abs(palavras[i]["start"] - em))]
    if not achados:
        return palavras, 0
    out, i, usados = [], 0, set(achados)
    while i < len(palavras):
        if i in usados:
            bloco = palavras[i: i + n]
            pre, pos = _separa(bloco[0]["word"])[0], _separa(bloco[-1]["word"])[2]
            ini, fim = bloco[0]["start"], bloco[-1]["end"]
            if len(certo) == n:              # mesma quantidade: mantém o tempo de cada palavra
                for k, (w, c) in enumerate(zip(bloco, certo)):
                    out.append({"word": (pre if k == 0 else "") + c + (pos if k == n - 1 else ""),
                                "start": w["start"], "end": w["end"]})
            else:                            # quantidade diferente: divide o tempo pelo tamanho das palavras
                pesos = [max(1, len(c)) for c in certo]
                total, t = sum(pesos), ini
                for k, (c, p) in enumerate(zip(certo, pesos)):
                    d = (fim - ini) * p / total
                    out.append({"word": (pre if k == 0 else "") + c + (pos if k == len(certo) - 1 else ""),
                                "start": round(t, 3), "end": round(t + d, 3)})
                    t += d
            i += n
        else:
            out.append(palavras[i])
            i += 1
    return out, len(achados)


def corrigir(video: Path, correcoes: list[str], em: float | None = None) -> int:
    video = video.resolve()
    reg = saida_registrada(video)
    if reg and reg.get("palavras") and Path(reg["palavras"]).exists():
        arquivo = Path(reg["palavras"])          # só as palavras deste vídeo; o original não muda
    else:
        job = pasta_job(video)
        arquivo = next((job / n for n in ("palavras.json", "palavras_direto.json") if (job / n).exists()), None)
    if not arquivo:
        raise CortaErro("Não achei palavras desse vídeo. Rode antes: corta transcrever (ou corta legendar).")
    palavras = ler_json(arquivo)
    total = 0
    for c in correcoes:
        if "=" not in c:
            raise CortaErro(f"Correção '{c}' precisa ser errado=certo (ex.: lerite=holerite).")
        errado, certo = c.split("=", 1)
        e_tokens, c_tokens = errado.split(), certo.split()
        if not e_tokens or not c_tokens:
            raise CortaErro(f"Correção '{c}' está vazia de um dos lados.")
        palavras, n = _aplicar(palavras, e_tokens, c_tokens, em)
        total += n
        log(f"   {errado} → {certo}: {n}×" + ("" if n else " (não achei; confira a grafia com 'corta texto')"))
    if total:
        salvar_json(arquivo, palavras)
        log(f"   salvo em {arquivo.name}")
    return total
