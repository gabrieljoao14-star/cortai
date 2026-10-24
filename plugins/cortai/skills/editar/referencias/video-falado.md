# Fluxo: um vídeo falado vira um vídeo editado

`M` = `"<PLUGIN>/bin/corta"`. `V` = caminho do vídeo entre aspas.

## 1. Voz e silêncio
`M preparar V --voz <voz> --ritmo <rapido|natural>`
Mostra quantos trechos de fala achou e quanto sai de pausa. Se achar fala em quase nada ou em tudo, algo
está estranho (vídeo sem voz, música alta): pare e conte à pessoa.

## 2. Erros de fala (se `erros-de-fala=sim`)
1. `M transcrever V` — transcrição literal (mantém repetições). Demora ~2× a duração da fala.
2. `M trechos V` — lista `T000 [início–fim] texto`. Trechos com ⚠ trazem também a leitura **isolada**: compare
   as duas, é ali que o recomeço escondido aparece.
3. Leia a lista inteira **como roteiro** e decida o que fica (critério abaixo). Escreva
   `<pasta do vídeo>/_corta/<nome>/takes.json`:
   ```json
   {"manter": [3, 4, [7, 12.40, null], 9],
    "notas": [["0:21", "tirado", "recomeço: Hoje eu vou…"], ["0:24", "MANTIDO", "último take completo"]]}
   ```
   Número = trecho inteiro; `[trecho, início, fim]` corta dentro do trecho (tempo do original; `null`
   mantém a borda). Para cortar dentro de um trecho com precisão, use os tempos das palavras em
   `_corta/<nome>/palavras.json`.
4. Mostre à pessoa a tabela **MANTIDO / tirado** com o porquê de cada tirado e os pontos de escolha
   ("ficou o último take do CTA; o anterior tinha 'clica aqui'"). Espere o ok (se `aprovacao` não for `direto`).

**Critério dos takes** (validado em dezenas de criativos):
- Frase recomeçada ou repetida: fica o **último take completo** (o que dá sequência ao roteiro), mesmo
  que as palavras mudem um pouco. Se o último perder algo importante, siga a regra e **avise** a alternativa.
- Sai toda fala de **quem está filmando** ("gravando", "pode seguir", "perfeito, agora o final",
  orientação de atuação, claquete, "luz ok, câmera ok, ação").
- Sai ênfase solta que não faz sentido sozinha, despedida e conversa depois do fim do take.
- Desconfie de: frase lenta demais para o número de palavras, palavra curta esticada ("é" de 0,8 s),
  palavra repetida em sequência ("Quem? Quem") — quase sempre é recomeço.

## 3. Montagem
`M montar V --takes "<…>/takes.json" --formato <formato> --enquadrar <enquadrar> --zoom <zoom>`
(sem `--takes` se `erros-de-fala=nao`). Sai `nome (editado).mp4`.
- `--formato` diferente do vídeo original recorta (ex.: horizontal → 9:16 segue o rosto).
- Gravação de aula/tutorial com tela + câmera: rode antes `M regioes V`, **abra `regioes.png`** e confira
  as caixas; depois `--enquadrar tela-camera`. Se a tela mostrar dado pessoal (processo, cliente, extrato)
  ou nada útil, use `--enquadrar camera` (só a câmera, sem a tela).

## 4. Texto da legenda
Rode `M texto "<editado>.mp4"` (o texto do vídeo **editado**, em frases, já no relógio dele) e procure
nomes, siglas, termos técnicos e números errados. **Não rode `preparar` nem `transcrever` no vídeo editado**:
as palavras dele já existem (o motor recusa e diz onde estão). Corrija:
`M corrigir "<editado>.mp4" "errado=certo" "duas palavras=certo"` (só mexe nas palavras do editado; a
pontuação é ignorada na busca; `--em 12.4` troca só a ocorrência perto desse segundo; palavra que faltou
entra assim: `"aquele aposentado=Sabe aquele aposentado"`).
Nome próprio que você não tem certeza: pergunte.

## 5. Gancho e CTA (se pedidos)
`sugerir`: proponha 2–3 opções e espere a escolha. Gancho com até ~10 palavras e na tela por **2,5 a 5 s**
(o motor corta em 5 s): é lido num relance, não é um parágrafo. Ache o `--cta-em` na transcrição (início
da fala da chamada).

## 6. Prévia
`M previa "<editado>.mp4" --estilo <estilo> --ajuste …` → abra a imagem e olhe: legenda legível, sem cobrir
o rosto, sem palavra cortada. Mostre à pessoa (a não ser `direto`).

## 7. Legenda e acabamento (uma gravação só)
`M legendar "<editado>.mp4" --estilo <estilo> [--ajuste …] [--gancho "…"] [--cta "…" --cta-em S] [--barra] [--sons poucos] [--trilha <estilo>] [--efeitos efeitos.json]`
Efeitos e trilha: ver [motion-e-trilha.md](motion-e-trilha.md) (inclui o ciclo de crítica).
Sai `nome (legendado).mp4`. Sem legenda mas com acabamento: `--estilo nenhuma`.

## 8. Conferência
1. `M quadros "<arquivo final>.mp4"` e **abra a imagem**: gancho legível e fora do rosto, legenda sem palavra
   cortada, CTA certo no fim. Se algo estiver errado, ajuste e grave de novo antes de entregar.
2. `M verificar "<arquivo final>.mp4"`. Explique o resultado:
- `[2]` aviso de "fala alta fora dos trechos": diga o trecho e o texto; geralmente é quem filma — se for
  fala de quem apresenta, refaça a montagem incluindo esse pedaço.
- `[4]` desvio > 2 quadros ou `[6]` atraso > 150 ms: a sincronia falhou — não entregue; rode
  `M diagnostico` e investigue.

## Vários vídeos (pasta com 2 ou mais vídeos)
1. Rode `M lote "<pasta>" --voz <voz> --ritmo <ritmo>` **em segundo plano**. Ele prepara, transcreve e lista
   os trechos de cada vídeo, um depois do outro, e escreve `PRONTO n/N: <vídeo>` a cada vídeo pronto
   (andamento em `<pasta>/_corta/lote.json`).
2. Assim que o 1º estiver PRONTO, leia `_corta/<nome>/trechos_texto.json` e decida os takes dele enquanto
   os outros processam. Não rode outro comando pesado (montar, legendar) ao mesmo tempo que o lote: fica
   3× mais lento. Monte e legende depois que o lote terminar, um vídeo por vez.
3. Junte as aprovações: mostre os takes de todos de uma vez (a não ser `aprovacao: direto`).
