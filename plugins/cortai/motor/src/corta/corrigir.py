"""Corrige palavras que o Whisper errou ("lerite" → "holerite", "Cloud" → "Claude").

Corrige só as palavras do vídeo indicado: um vídeo feito pelo Cortaí mexe só nas palavras dele (o
original fica intacto para ajustes e cortes futuros); o vídeo original mexe só no `palavras.json`.
Regras (achadas no teste real de 23/10):
- a pontuação colada na palavra é ignorada na busca e preservada no resultado ("aqui," acha "aqui,");
- "errado=certo" com mais palavras do lado certo cria palavras separadas, dividindo o tempo
  ("aquele aposentado=Sabe aquele aposentado" → 3 palavras, cada uma com seu destaque);
- `--em SEGUNDOS` troca só a ocorrência mais perto desse tempo (padrão: todas);
- correção que começa com "-" funciona (ex.: "-fé=fé").

Pontuação (achado em 13/11: trocar várias palavras deixava vírgula e ponto fora do lugar):
- a pontuação fica **no lugar**, não na palavra: "aqui, doutor=doutor aqui" dá "doutor, aqui";
- pontuação escrita do lado certo vale como está: "doutor aqui=doutor, aqui." põe a vírgula e o ponto;
- `--exato` troca **ao pé da letra**: acha só a palavra escrita daquele jeito (pontuação e maiúsculas
  contam) e escreve o lado certo como está ("advogado. E=advogado, e" · "certo?=certo." · "fim.=fim"
  tira o ponto);
- "errado|próxima=certo" troca só quando a palavra seguinte é `próxima` ("fim.|Mas=fim," troca o
  ponto só antes de "Mas"; a próxima não muda). Vale com e sem `--exato`.
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


def _bate(palavra: str, alvo: str, exato: bool) -> bool:
    if exato:
        return palavra.strip() == alvo
    return _miolo(palavra) == _miolo(alvo)


def _aplicar(palavras: list[dict], errado: list[str], certo: list[str], em: float | None,
             proxima: str | None = None, exato: bool = False) -> tuple[list[dict], int]:
    n = len(errado)
    achados = []
    for i in range(len(palavras) - n + 1):
        if not all(_bate(w["word"], e, exato) for w, e in zip(palavras[i: i + n], errado)):
            continue
        if proxima is not None:
            if i + n >= len(palavras) or not _bate(palavras[i + n]["word"], proxima, exato):
                continue
        if achados and i < achados[-1] + n:          # não sobrepõe a troca anterior ("a a a" com "a a=b")
            continue
        achados.append(i)
    if em is not None and achados:
        achados = [min(achados, key=lambda i: abs(palavras[i]["start"] - em))]
    if not achados:
        return palavras, 0

    def com_pontuacao(c: str, pre: str, pos: str) -> str:
        """`c` com a pontuação do lugar (pre/pos), a não ser a que já veio escrita em `c`."""
        if exato:
            return c
        c_pre, c_meio, c_pos = _separa(c)
        return (c_pre or pre) + c_meio + (c_pos or pos)

    out, i, usados = [], 0, set(achados)
    while i < len(palavras):
        if i in usados:
            bloco = palavras[i: i + n]
            ini, fim = bloco[0]["start"], bloco[-1]["end"]
            if len(certo) == n:              # mesma quantidade: mantém o tempo e a pontuação de cada lugar
                for w, c in zip(bloco, certo):
                    pre, _, pos = _separa(w["word"])
                    out.append({**w, "word": com_pontuacao(c, pre, pos)})
            else:                            # quantidade diferente: divide o tempo pelo tamanho das palavras
                pre, pos = _separa(bloco[0]["word"])[0], _separa(bloco[-1]["word"])[2]
                pesos = [max(1, len(c)) for c in certo]
                total, t = sum(pesos), ini
                for k, (c, p) in enumerate(zip(certo, pesos)):
                    d = (fim - ini) * p / total
                    out.append({**bloco[0], "word": com_pontuacao(c, pre if k == 0 else "", pos if k == len(certo) - 1 else ""),
                                "start": round(t, 3), "end": round(t + d, 3)})
                    t += d
            i += n
        else:
            out.append(palavras[i])
            i += 1
    return out, len(achados)


def corrigir(video: Path, correcoes: list[str], em: float | None = None, exato: bool = False) -> int:
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
        errado, _, proxima = errado.partition("|")
        proxima = proxima.strip() or None
        e_tokens, c_tokens = errado.split(), certo.split()
        if not e_tokens or not c_tokens:
            raise CortaErro(f"Correção '{c}' está vazia de um dos lados.")
        if proxima and len(proxima.split()) != 1:
            raise CortaErro(f"Correção '{c}': depois do | vai uma palavra só (a que vem logo em seguida).")
        palavras, n = _aplicar(palavras, e_tokens, c_tokens, em, proxima, exato)
        total += n
        onde = f" (antes de \"{proxima}\")" if proxima else ""
        log(f"   {errado.strip()}{onde} → {certo}: {n}×" + ("" if n else " (não achei; confira a grafia e a pontuação com 'corta texto')"))
    if total:
        salvar_json(arquivo, palavras)
        log(f"   salvo em {arquivo.name}")
    return total
