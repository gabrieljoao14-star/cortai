"""Comandos do motor. O Claude chama estes comandos; a pessoa normalmente nem vê.

  corta perfil [--recalcular]
  corta preparar VIDEO [--voz leve|forte|nao] [--ritmo rapido|natural]
  corta transcrever VIDEO [--idioma pt] [--modelo large-v2]
  corta trechos VIDEO [--isolado auto|todos|nenhum]
  corta montar VIDEO [--takes takes.json] [--apertar|--sem-apertar] [--saida ARQ]
               [--formato 9:16] [--enquadrar rosto|centro|desfocado|tela-camera] [--regioes ARQ] [--zoom nao|leve|normal|forte]
  corta legendar VIDEO [--estilo creator-bold|nenhuma] [--ajuste chave=valor …] [--saida ARQ]
                 [--gancho "pergunta | resposta"] [--cta "Toque em Saiba mais"] [--barra] [--sons poucos]
  corta previa VIDEO [--estilo …] [--em SEGUNDOS]
  corta corrigir VIDEO lerite=holerite ["lei rite=holerite" …]
  corta lote PASTA [--voz leve] [--ritmo rapido] [--sem-trechos]
  corta texto VIDEO
  corta cortar VIDEO --cortes cortes.json [--formato 9:16] [--enquadrar rosto] [--zoom leve] [--legenda ESTILO]
  corta regioes VIDEO [--de S --ate S]   (tela + câmera de aula/tutorial)
  corta quadros VIDEO [--em S …] [--n 8]   (folha para olhar o vídeo pronto)
  corta chave elevenlabs [--status|--remover]   (no Terminal: a chave não aparece)
  corta vozes · corta voz --texto ROTEIRO.txt --voz NOME --saida narracao
  corta narracao --audio voz.m4a --saida narracao  (ou --texto roteiro.txt --voz NOME)
  corta animacao --cenas cenas.json --narracao narracao.wav --palavras narracao.json --saida video.mp4
  corta trilha --estilo emocional --duracao 60 --saida trilha.wav
  corta estilos
  corta verificar SAIDA
  corta amostra
  corta diagnostico
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .base import CortaErro, configurar_saida_utf8, encerrar_filhos, log, proteger_filhos, supervisionar


def _ajustes(lista):
    out = {}
    for item in lista or []:
        if "=" not in item:
            raise CortaErro(f"Ajuste '{item}' precisa ser chave=valor (ex.: cor=#FFFFFF).")
        k, v = item.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def main(argv=None):
    configurar_saida_utf8()
    codigo = supervisionar(sys.argv[1:] if argv is None else list(argv))
    if codigo is not None:
        sys.exit(codigo)
    proteger_filhos()
    ap = argparse.ArgumentParser(prog="corta", description="Motor de edição do Cortaí")
    ap.add_argument("--version", action="version", version=f"corta {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("perfil", help="mede o computador e escolhe as configurações")
    p.add_argument("--recalcular", action="store_true")

    p = sub.add_parser("preparar", help="voz limpa + onde tem fala")
    p.add_argument("video", type=Path)
    p.add_argument("--voz", default=None, choices=["leve", "forte", "nao"])
    p.add_argument("--ritmo", default="rapido", choices=["rapido", "natural"])

    p = sub.add_parser("transcrever", help="transcrição literal por palavra")
    p.add_argument("video", type=Path)
    p.add_argument("--idioma", default="pt")
    p.add_argument("--modelo", default=None)

    p = sub.add_parser("trechos", help="lista numerada dos trechos com o texto")
    p.add_argument("video", type=Path)
    p.add_argument("--isolado", default="auto", choices=["auto", "todos", "nenhum"])
    p.add_argument("--idioma", default="pt")

    p = sub.add_parser("montar", help="monta o vídeo só com o que fica")
    p.add_argument("video", type=Path)
    p.add_argument("--takes", type=Path)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--apertar", dest="apertar", action="store_true", default=None)
    g.add_argument("--sem-apertar", dest="apertar", action="store_false")
    p.add_argument("--saida", type=Path)
    p.add_argument("--formato", default=None, choices=["original", "9:16", "4:5", "1:1", "16:9"])
    p.add_argument("--enquadrar", default="rosto", choices=["rosto", "centro", "desfocado", "tela-camera", "camera"])
    p.add_argument("--zoom", default="nao", choices=["nao", "leve", "normal", "forte"])
    p.add_argument("--regioes", type=Path, help="caixas da tela e da câmera (padrão: detectar)")

    for nome in ("legendar", "previa"):
        p = sub.add_parser(nome, help="queima a legenda" if nome == "legendar" else "quadro de prévia da legenda")
        p.add_argument("video", type=Path)
        p.add_argument("--estilo", default="creator-bold")
        p.add_argument("--ajuste", action="append", metavar="CHAVE=VALOR")
        p.add_argument("--palavras", type=Path, help="palavras com tempo (padrão: as da montagem)")
        p.add_argument("--idioma", default="pt")
        if nome == "legendar":
            p.add_argument("--saida", type=Path)
            p.add_argument("--gancho", default=None, help='texto no topo; "pergunta | resposta" faz 2 níveis')
            p.add_argument("--gancho-ate", type=float, default=None, help="segundo em que o gancho sai (padrão: fim da 1ª frase)")
            p.add_argument("--cta", default=None, help='chamada no final, ex.: "Toque em Saiba mais"')
            p.add_argument("--cta-em", type=float, default=None, help="segundo em que a chamada entra (padrão: 4 s antes do fim)")
            p.add_argument("--barra", action="store_true", help="barra de progresso no topo")
            p.add_argument("--sons", default="nao", choices=["nao", "poucos", "todos"])
            p.add_argument("--trilha", default="nao",
                           choices=["nao", "emocional", "corporativo", "tensao", "lofi", "epico", "energia"])
            p.add_argument("--trilha-arquivo", type=Path, help="música da própria pessoa (mp3/wav)")
            p.add_argument("--efeitos", type=Path, help="efeitos.json com os efeitos de motion (Remotion)")
        else:
            p.add_argument("--em", type=float, default=None, help="segundo do vídeo (padrão: meio da 1ª frase)")

    p = sub.add_parser("corrigir", help="corrige palavras erradas da transcrição (errado=certo)")
    p.add_argument("--em", type=float, default=None, help="troca só a ocorrência mais perto deste segundo")
    p.add_argument("video", type=Path)
    p.add_argument("correcoes", nargs=argparse.REMAINDER, metavar="ERRADO=CERTO")

    p = sub.add_parser("quadros", help="folha de quadros do vídeo pronto, para olhar antes de entregar")
    p.add_argument("video", type=Path)
    p.add_argument("--em", type=float, nargs="*", help="segundos exatos (padrão: gancho, CTA e pontos espalhados)")
    p.add_argument("--n", type=int, default=8)

    p = sub.add_parser("lote", help="prepara, transcreve e lista os trechos de todos os vídeos de uma pasta")
    p.add_argument("pasta", type=Path)
    p.add_argument("--voz", default=None, choices=["leve", "forte", "nao"])
    p.add_argument("--ritmo", default="rapido", choices=["rapido", "natural"])
    p.add_argument("--idioma", default="pt")
    p.add_argument("--sem-trechos", action="store_true", help="só prepara e transcreve (para cortes de vídeo longo)")

    p = sub.add_parser("texto", help="transcrição em frases com o tempo (para escolher cortes)")
    p.add_argument("video", type=Path)

    p = sub.add_parser("cortar", help="gera os cortes de um vídeo longo a partir de cortes.json")
    p.add_argument("video", type=Path)
    p.add_argument("--cortes", type=Path, required=True)
    p.add_argument("--formato", default="9:16", choices=["original", "9:16", "4:5", "1:1", "16:9"])
    p.add_argument("--enquadrar", default="rosto", choices=["rosto", "centro", "desfocado", "tela-camera", "camera"])
    p.add_argument("--zoom", default="nao", choices=["nao", "leve", "normal", "forte"])
    p.add_argument("--regioes", type=Path, help="caixas da tela e da câmera (padrão: detectar)")
    p.add_argument("--legenda", default=None, metavar="ESTILO")
    p.add_argument("--ajuste", action="append", metavar="CHAVE=VALOR")
    p.add_argument("--takes", type=Path)
    p.add_argument("--cta", default=None)
    p.add_argument("--barra", action="store_true")
    p.add_argument("--sons", default="nao", choices=["nao", "poucos", "todos"])
    p.add_argument("--trilha", default=None, choices=["nao", "emocional", "corporativo", "tensao", "lofi", "epico", "energia"])

    p = sub.add_parser("regioes", help="acha a tela e a câmera numa gravação de aula/tutorial")
    p.add_argument("video", type=Path)
    p.add_argument("--de", type=float, default=0.0)
    p.add_argument("--ate", type=float, default=None)

    p = sub.add_parser("trilha", help="compõe só a trilha (para Só animação ou para ouvir os estilos)")
    p.add_argument("--estilo", required=True, choices=["emocional", "corporativo", "tensao", "lofi", "epico", "energia"])
    p.add_argument("--duracao", type=float, required=True)
    p.add_argument("--saida", type=Path, required=True)
    p.add_argument("--impactos", type=float, nargs="*", default=[])
    p.add_argument("--cta-em", type=float, default=None)

    p = sub.add_parser("chave", help="conecta uma chave (ex.: ElevenLabs) — fica só neste computador")
    p.add_argument("servico", choices=["elevenlabs"])
    g = p.add_mutually_exclusive_group()
    g.add_argument("--remover", action="store_true")
    g.add_argument("--status", action="store_true")

    sub.add_parser("vozes", help="lista as vozes da ElevenLabs")
    p = sub.add_parser("voz", help="gera narração com a ElevenLabs (mp3 + palavras com tempo)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--texto", type=Path, help="arquivo .txt com o roteiro")
    g.add_argument("--frase", help="texto curto direto no comando")
    p.add_argument("--voz", required=True, help="nome ou id da voz (veja: corta vozes)")
    p.add_argument("--saida", type=Path, required=True)

    p = sub.add_parser("narracao", help="Só animação: narração (ElevenLabs ou áudio próprio) com o tempo das palavras")
    p.add_argument("--saida", type=Path, required=True)
    p.add_argument("--audio", type=Path, help="áudio gravado pela pessoa")
    p.add_argument("--texto", type=Path, help="roteiro .txt (para a ElevenLabs)")
    p.add_argument("--voz", help="voz da ElevenLabs (nome ou id)")
    p.add_argument("--idioma", default="pt")

    p = sub.add_parser("animacao", help="Só animação: grava as cenas no Remotion no tempo da narração")
    p.add_argument("--cenas", type=Path, required=True)
    p.add_argument("--narracao", type=Path, required=True)
    p.add_argument("--palavras", type=Path)
    p.add_argument("--saida", type=Path, required=True)
    p.add_argument("--formato", default="9:16", choices=["9:16", "4:5", "1:1", "16:9"])

    sub.add_parser("estilos", help="lista os estilos de legenda e de trilha")

    p = sub.add_parser("verificar", help="confere a saída (duração, sincronia, fala removida, legenda)")
    p.add_argument("saida", type=Path)

    sub.add_parser("amostra", help="edita o vídeo de amostra e confere (teste da instalação)")
    sub.add_parser("diagnostico", help="confere se o computador está pronto e diz o que consertar")
    sub.add_parser("versao", help="versão instalada, se há versão nova no GitHub e se o instalador rodou")

    a = ap.parse_args(argv)
    if a.cmd not in ("perfil", "estilos", "diagnostico", "texto", "corrigir", "chave", "vozes", "versao"):
        from .base import manter_acordado
        manter_acordado()
    try:
        if a.cmd == "perfil":
            from .perfil import carregar, mostrar
            mostrar(carregar(recalcular=a.recalcular))
        elif a.cmd == "preparar":
            from .perfil import carregar
            from .preparar import preparar
            preparar(a.video, voz=a.voz or carregar()["voz_padrao"], ritmo=a.ritmo)
        elif a.cmd == "transcrever":
            from .transcrever import transcrever
            transcrever(a.video, idioma=a.idioma, nome_modelo=a.modelo)
        elif a.cmd == "trechos":
            from .trechos import listar
            listar(a.video, isolado=a.isolado, idioma=a.idioma)
        elif a.cmd == "montar":
            from .montar import montar
            montar(a.video, takes=a.takes, apertar=a.apertar, saida=a.saida, formato=a.formato,
                   enquadrar=a.enquadrar, zoom=a.zoom, regioes=a.regioes)
        elif a.cmd == "legendar":
            from .legenda.queimar import legendar
            legendar(a.video, estilo=a.estilo, ajustes=_ajustes(a.ajuste), palavras=a.palavras, idioma=a.idioma, saida=a.saida,
                     gancho=a.gancho, gancho_ate=a.gancho_ate, cta=a.cta, cta_em=a.cta_em, barra=a.barra, sons=a.sons,
                     trilha=a.trilha, trilha_arquivo=a.trilha_arquivo, efeitos=a.efeitos)
        elif a.cmd == "previa":
            from .legenda.queimar import previa
            previa(a.video, estilo=a.estilo, ajustes=_ajustes(a.ajuste), palavras=a.palavras, idioma=a.idioma, em=a.em)
        elif a.cmd == "corrigir":
            from .corrigir import corrigir
            if not a.correcoes:
                raise CortaErro("Diga o que corrigir, ex.: corta corrigir VIDEO lerite=holerite")
            corrigir(a.video, a.correcoes, em=a.em)
        elif a.cmd == "quadros":
            from .folha import quadros
            quadros(a.video, em=a.em, n=a.n)
        elif a.cmd == "lote":
            from .lote import lote
            from .perfil import carregar
            lote(a.pasta, voz=a.voz or carregar()["voz_padrao"], ritmo=a.ritmo, idioma=a.idioma, com_trechos=not a.sem_trechos)
        elif a.cmd == "texto":
            from .cortes import texto
            texto(a.video)
        elif a.cmd == "cortar":
            from .cortes import cortar
            cortar(a.video, a.cortes, formato=a.formato, enquadrar=a.enquadrar, zoom=a.zoom, legenda=a.legenda,
                   ajustes=_ajustes(a.ajuste), takes=a.takes, regioes=a.regioes, cta=a.cta, barra=a.barra, sons=a.sons,
                   trilha=a.trilha)
        elif a.cmd == "regioes":
            from .regioes import detectar
            detectar(a.video, a.de, a.ate)
        elif a.cmd == "chave":
            from .voz import conectar, desconectar, status
            desconectar() if a.remover else status() if a.status else conectar()
        elif a.cmd == "vozes":
            from .voz import vozes
            vozes()
        elif a.cmd == "voz":
            from .voz import falar
            texto = a.texto.read_text(encoding="utf-8") if a.texto else a.frase
            falar(texto, a.voz, a.saida)
        elif a.cmd == "narracao":
            from .animacao import narracao
            narracao(a.saida, texto=a.texto.read_text(encoding="utf-8") if a.texto else None, voz=a.voz, audio=a.audio,
                     idioma=a.idioma)
        elif a.cmd == "animacao":
            from .animacao import animacao
            animacao(a.cenas, a.narracao, a.palavras, a.saida, formato=a.formato)
        elif a.cmd == "trilha":
            from .trilha import gerar
            gerar(a.estilo, a.duracao, a.saida, impactos=a.impactos, cta_em=a.cta_em)
        elif a.cmd == "estilos":
            from .legenda.estilos import listar_estilos
            from .trilha import estilos as estilos_trilha
            listar_estilos()
            log("\nTrilhas:")
            for k, v in estilos_trilha().items():
                log(f"{k:18s} {v}")
        elif a.cmd == "verificar":
            from .verificar import verificar
            ok = verificar(a.saida)
            sys.exit(0 if ok else 2)
        elif a.cmd == "versao":
            from .versao import versao
            versao()
        elif a.cmd == "diagnostico":
            from .diagnostico import diagnostico
            sys.exit(0 if diagnostico() else 2)
        elif a.cmd == "amostra":
            from .amostra import amostra
            sys.exit(0 if amostra() else 2)
    except CortaErro as e:
        log(f"❌ {e}")
        sys.exit(1)
    except BrokenPipeError:          # saída mandada para `head` e fechada antes do fim: não é erro
        sys.stderr.close()
        sys.exit(0)
    except KeyboardInterrupt:
        encerrar_filhos()
        log("⏹ interrompido")
        sys.exit(130)


if __name__ == "__main__":
    main()
