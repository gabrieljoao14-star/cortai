---
name: editar
description: >-
  Edita vídeos a partir de uma receita do Cortaí — tira silêncio e erros de fala, legenda em estilos do CapCut, zoom no rosto, cortes de vídeo longo, efeitos de motion, trilha, gancho, CTA e vídeos só de animação com narração — e confere o resultado. Use quando a pessoa colar uma receita que começa com "/cortai:editar" ou "receita: cortai/" (ou "corta/"), ou pedir para editar, legendar, tirar silêncio, tirar erros de fala, fazer cortes/shorts/reels ou uma animação com o Cortaí.
---

# Cortaí — editar a partir da receita

Você conduz a edição; quem corta, legenda e confere é o **motor** do plugin. **Nunca escreva comandos de
ffmpeg na mão nem edite vídeo de outro jeito**: rode só os comandos do motor. Eles já foram testados no
Mac e no Windows e conferem o próprio trabalho.

## Como chamar o motor
A pasta do plugin é a pasta **duas acima desta skill** (o "Base directory" desta skill termina em
`skills/editar`). Chame sempre o lançador com o caminho completo e entre aspas:

```bash
"<PLUGIN>/bin/corta" <comando> …
```

Exemplo: se a skill está em `/Users/ana/.claude/plugins/cache/cortai/cortai/0.6.0/skills/editar`, o motor é
`"/Users/ana/.claude/plugins/cache/cortai/cortai/0.6.0/bin/corta"` (o motor se chama `corta`). No Windows o mesmo lançador roda no
Bash do Claude Code. Caminhos de vídeo sempre entre aspas (têm espaço e acento).

**Antes de tudo**, rode `"<PLUGIN>/bin/corta" versao` e leia a última linha:
- falhou (o motor nem abre): o Cortaí não foi instalado neste computador — siga a skill `/cortai:instalar`
  e só depois edite;
- `ESTADO: instalar`: o plugin foi atualizado mas o instalador não rodou nesta versão. Diga em uma linha
  "o Cortaí foi atualizado; vou preparar a versão nova (uns 5 min)", siga a skill `/cortai:instalar` e
  depois continue a edição;
- `ESTADO: atualizar`: existe versão mais nova. Dê o aviso da linha ⚠ em uma frase e **continue a edição**
  com a versão atual (não atualize no meio de uma edição);
- `ESTADO: ok`: siga.

## 1. Ler a receita
O formato está em [referencias/receita.md](referencias/receita.md). Campos que faltarem usam o padrão de lá.

**A pasta.** A receita do app termina em `pasta:` e a pessoa arrasta a pasta logo depois. O caminho pode
chegar de vários jeitos: entre aspas, com `\ ` antes dos espaços, com `@` na frente, com barra invertida do
Windows (`C:\Users\ana\Vídeos`) ou numa linha separada. Limpe isso e confira que a pasta existe
(`ls "<pasta>"`). Também vale um arquivo de vídeo em vez de pasta.
- `pasta:` vazia, sem nada arrastado: peça **"arraste a pasta com os vídeos para esta conversa e aperte Enter"**
  e espere. Não procure vídeos pelo computador.
- Vídeos = arquivos `.mp4 .mov .m4v .mkv .webm .avi` da pasta (não entre em subpastas; ignore o que já tem
  `(editado)`, `(legendado)`, `(final)` ou `(A)`…`(H)` no nome: são saídas do Cortaí). **1 vídeo** → edição normal.
  **2 ou mais** → vários vídeos (automatico-e-lote.md); sem `lote:` na receita, use `iguais`.
- Fotos (`.png .jpg .jpeg .webp`) e áudios (`.mp3 .m4a .wav`) da pasta são material: produto/logo para o
  efeito `imagem`, música para `trilha=arquivo`, voz gravada para `voz: audio`.
- Nenhum vídeo na pasta (e não é `tipo: animacao`): diga o que encontrou e peça o vídeo.

Diga em 2–3 linhas o que vai fazer e quanto tempo leva (tabela de tempos em
[referencias/comandos.md](referencias/comandos.md)). Vídeo de mais de ~8 min ou transcrição/montagem que
passe de 10 min: rode o comando **em segundo plano** e acompanhe; não deixe o comando estourar o tempo.

## 2. Escolher o fluxo
- `tipo: animacao` (vídeo inteiro de motion, sem pessoa gravando): siga [referencias/so-animacao.md](referencias/so-animacao.md).
- `formato: cortes` ou `tipo: cortes` (live, aula, podcast → vários vídeos curtos): siga [referencias/cortes.md](referencias/cortes.md).
- Qualquer outro (um vídeo falado vira um vídeo editado): siga [referencias/video-falado.md](referencias/video-falado.md).
- `pasta:` (vários vídeos), qualquer `automatico` ou `especial:`: leia também
  [referencias/automatico-e-lote.md](referencias/automatico-e-lote.md). O `especial` é lido antes de tudo.
- Efeitos de motion e trilha sonora (`efeitos=`, `trilha=`): leia também
  [referencias/motion-e-trilha.md](referencias/motion-e-trilha.md) — inclui o **ciclo de crítica obrigatório**.
- Só legenda/acabamento num vídeo já pronto (`limpeza: silencio=nao · erros-de-fala=nao`): pule direto
  para `legendar` (ele transcreve sozinho).

## 3. Regras que valem sempre
1. **Nunca sobrescreva** o original nem uma saída anterior (o motor já cria `nome (2).mp4`). Não apague
   vídeos da pessoa.
2. **Decisão de conteúdo é da pessoa**: quais takes ficam, quais trechos viram corte, texto do gancho e do
   CTA, correção de nome próprio. Mostre a lista e espere o "ok" — a não ser que a receita diga
   `aprovacao: direto`. O que é técnico (sincronia, volume, posição) você confere sozinho.
3. **Mostre antes de gravar o vídeo inteiro**: rode `previa`, abra a imagem (Read) e olhe você mesmo antes
   de mostrar. Legenda cobrindo o rosto, palavra cortada na borda ou texto ilegível: ajuste antes.
4. **Confira no fim** com `verificar` e conte o resultado com honestidade: `OK ✅`, `OK com avisos`
   (explique cada aviso) ou `ATENÇÃO` (não entregue como pronto: investigue e corrija).
5. Transcrição erra nomes e termos técnicos: leia o texto antes de legendar e corrija com `corrigir`
   (nome de pessoa/marca na dúvida: pergunte).
6. Fale com a pessoa em português simples. Nada de jargão técnico na conversa.
7. No fim, diga onde estão os arquivos e que a pasta `_corta` ao lado do vídeo guarda os dados da edição
   (pode apagar depois de aprovar, mas sem ela não dá para fazer ajustes rápidos).

## 4. Ajustes depois da entrega
Pedidos como "troca o take do final", "corrige a palavra X", "legenda amarela", "tira o gancho": refaça só
a etapa necessária com os dados que já estão em `_corta` (não transcreva de novo). Ex.: mudar a cor da
legenda = só `legendar` de novo com `--ajuste destaque=#…`.

Se algo do motor falhar de um jeito que você não entende, rode `"<PLUGIN>/bin/corta" diagnostico` e siga o
que ele disser.
