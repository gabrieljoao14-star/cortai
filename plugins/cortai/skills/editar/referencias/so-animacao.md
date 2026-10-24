# Só animação (vídeo inteiro de motion, sem pessoa gravando)

`M` = `"<PLUGIN>/bin/corta"`. Receita com `tipo: animacao`. Resultado: vídeo com cenas animadas no tempo
exato da narração, legenda nas partes sem texto, trilha e sons.

## 1. Roteiro
- Receita com `roteiro: "…"`: use o texto como está (só corrija erro de digitação).
- Receita só com `tema: "…"`: escreva o roteiro. Regras: gancho na 1ª frase (pergunta, número ou dor),
  frases curtas, uma ideia por frase, termina com a chamada (`cta`). Tamanho pela `duracao`
  (~2,5 palavras por segundo: 30 s ≈ 75 palavras). Mostre e espere o "ok" (a não ser `aprovacao: direto`).
- Nunca invente número, estudo ou resultado. Se o tema pede dado, use o que a pessoa deu ou fale sem número.

## 2. Narração
| Receita | Comando |
|---|---|
| `voz: audio` ou `audio="<arquivo>"` (a pessoa gravou; sem arquivo = o áudio que está na pasta) | `M narracao --audio "<arquivo>" --saida "<pasta>/narracao"` |
| `voz: elevenlabs=<nome>` | salve o roteiro em `<pasta>/roteiro.txt` e rode `M narracao --texto "<pasta>/roteiro.txt" --voz "<nome>" --saida "<pasta>/narracao"` |
| `voz: elevenlabs` sem nome | `M vozes` e escolha uma que combine (mostre 2–3 opções se `aprovacao` não for `direto`) |

Sai `narracao.wav`/`.mp3` e `narracao.json` (palavras com tempo). Se o áudio próprio tiver roteiro na
receita, confira que a transcrição bate com ele (só para achar os tempos; o áudio não muda).

**Chave da ElevenLabs:** se `M chave elevenlabs --status` disser que não está conectada, **não peça a chave
no chat**. Diga à pessoa: "abra o Terminal (no Windows: PowerShell) e rode
`~/.corta/bin/corta chave elevenlabs` (Windows: `%USERPROFILE%\.corta\bin\corta.cmd chave elevenlabs`), cole a
chave quando ele pedir e me avise". A chave fica só no computador dela. Sem chave: ofereça gravar o áudio
no celular e arrastar o arquivo para a conversa.

## 2b. Estilo antes das cenas (método do curso do Movez)
Antes de escrever as cenas, escreva dois arquivos curtos na pasta e siga os dois até o fim:
1. **`style_guide.md`**: cor de fundo, **uma** cor de destaque (a da marca, se houver em `especial` ou num
   logo da pasta), fonte dos títulos e o "jeito" do movimento (seco e rápido para vendas; mais lento e com
   respiro para saúde/jurídico). Se a pasta tiver um vídeo ou imagem de referência, tire o estilo dele:
   abra 3–4 quadros (`M quadros "<referência>" --n 4`) e descreva o que vê, sem copiar marca de ninguém.
2. **`shotlist.md`**: uma linha por cena, no tempo da narração: segundo, frase dita, o que aparece, tipo de
   cena. É aqui que se confere a regra "algo novo a cada 2–4 s" e que nada se repete.
Só depois disso escreva `cenas.json` (ele é a shotlist em formato de máquina).

## 3. Cenas (`<pasta>/cenas.json`)
Leia `narracao.json` e ancore cada cena na palavra em que a ideia começa (`inicio` = `start` dessa
palavra, `fim` = início da próxima cena). A última cena vai até o fim da narração + 0,5 s.

```json
{"destaque": "#FFE14D", "cor_fundo": "#101114", "cenas": [
  {"tipo": "titulo",          "inicio": 0.0, "fim": 2.0,  "props": {"texto": "Você está perdendo dinheiro", "chave": "dinheiro"}},
  {"tipo": "contador",        "inicio": 2.0, "fim": 4.3,  "props": {"de": 0, "ate": 7000, "prefixo": "R$ ", "rotulo": "por mês"}},
  {"tipo": "frase",           "inicio": 4.3, "fim": 6.9,  "props": {"antes": "O segredo é", "marcado": "cortar", "depois": "o que não vende"}},
  {"tipo": "imagem",          "inicio": 6.9, "fim": 9.0,  "props": {"arquivo": "produto.png", "legenda": "MenoPro"}},
  {"tipo": "lista",           "inicio": 9.0, "fim": 12.1, "props": {"titulo": "3 passos", "itens": ["Medir", "Cortar", "Repetir"]}},
  {"tipo": "palavra-gigante", "inicio": 12.1,"fim": 13.9, "props": {"texto": "agora"}}
]}
```
| Cena | Para | Texto máximo |
|---|---|---|
| `titulo` | abertura, virada de assunto (palavras entram uma a uma; `chave` fica na cor de destaque) | 6 palavras |
| `frase` | a ideia principal de um trecho (faixa pinta a parte `marcado`) | 10 palavras |
| `palavra-gigante` | 1–2 palavras de impacto | 2 palavras |
| `contador` | número dito (R$, %, quantidade) | — |
| `lista` | enumeração (itens entram um a um) | 4 itens de 3 palavras |
| `grafico` | comparação com números de verdade | 4 barras |
| `manchetes` | "todo mundo está falando de…" (só manchete real) | 3 itens |
| `imagem` | foto da pasta da pessoa (`arquivo`); PNG transparente vira produto solto com sombra | legenda de 4 palavras |
| `emoji` | emoção, humor, alerta (`emoji`, `pos`) | — |
| `nome-cargo` | apresentar quem fala ou a marca | — |

Regras (método do curso do Movez, validado pelo sócio do João):
1. **Algo novo a cada 2–4 s.** Cena de mais de 4 s: divida (ex.: título → palavra gigante).
2. **A tela mostra a ideia, não a frase inteira**: resuma a fala em poucas palavras.
3. Varie: nunca 2 cenas seguidas do mesmo tipo. Uma cor de destaque só (a da legenda/marca).
4. A primeira cena é o gancho: `titulo` ou `palavra-gigante`, entra em até 0,3 s.
5. Imagens da pasta da pessoa (produto, print, antes/depois) valem mais que texto: use quando houver.
6. Nas cenas com texto a legenda some sozinha (sem texto duplicado). `"legenda": true` na cena força a
   legenda; `"legenda": false` tira.

## 4. Gravar, acabar e conferir
```bash
M animacao --cenas "<pasta>/cenas.json" --narracao "<pasta>/narracao.wav" --palavras "<pasta>/narracao.json" --saida "<pasta>/<nome>.mp4" [--formato 9:16]
M legendar "<pasta>/<nome>.mp4" --estilo <estilo> --ajuste posicao=baixo --trilha <estilo> --sons poucos [--cta "…"] --saida "<pasta>/<nome> final.mp4"
M quadros "<pasta>/<nome> final.mp4" --em <um segundo dentro de cada cena>
```
- Gravar leva ~1,5 s por segundo de vídeo; o acabamento, segundos.
- **Ciclo de crítica obrigatório** (igual ao dos efeitos, em motion-e-trilha.md): abra a folha, dê nota
  1–10 em leitura no celular, uma ideia por cena, variedade, ritmo com a fala e acabamento. Corrija as 3
  piores no `cenas.json`, grave de novo e repita até tudo ficar 8+. Diga as notas na entrega.
- `M verificar "<final>.mp4"` no fim (sincronia de imagem e som).
- Formato: `9:16` (padrão), `4:5`, `1:1`, `16:9`.
