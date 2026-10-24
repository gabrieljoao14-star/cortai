# Comandos do motor e tempos

`M` = `"<PLUGIN>/bin/corta"`. `M <comando> --help` mostra todas as opções.

| Comando | Faz | Tempo aproximado (Mac M2, sem placa de vídeo) |
|---|---|---|
| `M preparar V [--voz leve|forte|nao] [--ritmo rapido|natural]` | voz limpa + onde tem fala | ~10 % da duração (forte: ~30 %) |
| `M transcrever V` | transcrição literal por palavra | ~1,7× a duração da **fala** (7:35 de vídeo com 4:12 de fala = 7,3 min) |
| `M trechos V [--isolado auto|todos|nenhum]` | lista de trechos para os takes | ~10 s por trecho suspeito (gravação com muitos recomeços: ~5 min) |
| `M lote PASTA [--voz] [--ritmo] [--sem-trechos]` | prepara + transcreve + trechos de todos os vídeos da pasta | soma dos vídeos (rode em segundo plano) |
| `M montar V [--takes T] [--formato] [--enquadrar] [--zoom] [--regioes R]` | monta o vídeo | ~25 % da duração original |
| `M corrigir [--em S] SAIDA "errado=certo" …` | corrige palavra da transcrição (só deste vídeo) | instantâneo |
| `M texto V` | transcrição em frases com tempo | instantâneo |
| `M regioes V [--de S --ate S]` | acha tela e câmera (aula/tutorial) | ~30 s |
| `M cortar V --cortes C …` | gera os cortes | ~1 min por corte |
| `M previa SAIDA --estilo E [--ajuste …] [--em S]` | 3 quadros com a legenda | segundos |
| `M legendar SAIDA --estilo E [--ajuste …] [--gancho] [--cta] [--cta-em] [--barra] [--sons] [--trilha] [--efeitos]` | legenda e acabamento | ~50 % da duração (+ ~15 s por efeito novo) |
| `M quadros SAIDA [--em S …]` | folha com quadros do vídeo pronto (gancho, meio, CTA) para olhar | segundos |
| `M verificar SAIDA` | conferência independente | 1–2 min |
| `M narracao --saida S (--audio A | --texto T.txt --voz V)` | narração com palavras no tempo (áudio próprio ou ElevenLabs) | segundos (áudio próprio: transcreve) |
| `M animacao --cenas C --narracao N --palavras P --saida S [--formato]` | grava o vídeo só de animação | ~1,5 s por segundo de vídeo |
| `M vozes` / `M chave elevenlabs --status` | vozes da ElevenLabs / se a chave está conectada | segundos |
| `M estilos` | lista os estilos de legenda e de trilha | — |
| `M perfil` | o que este computador usa (modelo, gravação) | — |
| `M diagnostico` | confere a instalação e diz o que consertar | segundos |

Windows sem placa NVIDIA: transcrição ~2–4× mais lenta que a tabela. Com NVIDIA: bem mais rápida.
**Um comando pesado por vez** (preparar, transcrever, trechos, lote, montar, legendar): dois ao mesmo tempo
dividem o processador e cada um leva 2–3× mais (teste de 23/10: 13 min de fala levaram 78 min com um lote
rodando junto). Diga à pessoa para não editar duas pastas ao mesmo tempo no mesmo computador.

## Ajustes de legenda (`--ajuste chave=valor`)
`fonte` (Montserrat, Poppins, Anton, Bebas Neue, Luckiest Guy, DM Sans, Playfair Display, Inter, Courier Prime) ·
`cor`, `destaque`, `cor_contorno`, `cor_brilho`, `fundo_bloco` (#RRGGBB) ·
`tipo_destaque` (cor, caixa, escala, sublinhado, nenhum) · `contorno` (0–20) · `sombra` · `brilho` ·
`palavras` (1–8) · `tamanho` (0,4–2,5) · `posicao` (baixo, centro, topo) ·
`animacao` (pop, pulo, aparecer, subir, nenhuma) · `letras` (maiusculas, normal, minusculas) ·
`giro_destaque` · `escala_destaque` · `emoji` (sim, nao: emoji automático nas palavras-chave, em qualquer estilo).

Estilos (`M estilos`): creator-bold, caixa-na-palavra, karaoke, palavra-unica, faixa-de-fundo, classica,
minimal, neon, cartoon, **maquina-de-escrever** (palavras aparecem conforme são ditas), **hierarquia**
(palavra-chave enorme), **editorial** (palavra-chave em serifa itálica), **com-emoji**.

## Onde ficam os dados
`<pasta do vídeo>/_corta/<nome>/`: `voz.wav`, `trechos.json`, `palavras.json`, `takes.json`,
`mapa_*.json`, `palavras_*.json`, `rosto.json`, `regioes.json`, prévias e relatórios de conferência.
