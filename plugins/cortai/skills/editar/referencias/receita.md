# Formato da receita (versão 1)

A receita vem do app Cortaí (ou é escrita à mão). Uma linha por campo, `campo: valor`; opções separadas
por `·`. Campos que faltarem usam o padrão. Linha que você não reconhecer: ignore e avise a pessoa.

```
/cortai:editar
receita: cortai/1 · Reels falado rápido
formato: 9:16
limpeza: silencio=rapido · erros-de-fala=sim · voz=leve
legenda: creator-bold
  ajustes: fonte=Montserrat · destaque=#FFE14D · palavras=3 · posicao=baixo · animacao=pop · letras=maiusculas
movimento: zoom=normal · enquadrar=rosto · efeitos=automatico
acabamento: gancho=sugerir · cta="Toque em Saiba mais" · barra=sim · sons=poucos · trilha=automatico
aprovacao: conteudo
idioma: pt
videos:
  - /Users/ana/Videos/gravacao 1.mov
```

Vários vídeos de uma vez: `pasta: /Users/ana/Videos/criativos` + `lote: iguais|diferentes|automatico` no lugar
de `videos:`. Pedido livre da pessoa: `especial: "mostrar o produto.png quando falar do frasco"`.

Só animação (sem pessoa gravando):
```
/cortai:editar
receita: cortai/1 · Só animação
tipo: animacao
formato: 9:16
animacao: tema="3 erros de quem começa a vender online" · duracao=30
voz: elevenlabs=Rachel            (ou: audio="/Users/ana/Videos/minha voz.m4a")
legenda: automatico
acabamento: trilha=automatico · sons=poucos · cta="Siga para mais"
aprovacao: conteudo
pasta: /Users/ana/Videos/animacao
```

| Campo | Valores | Padrão | Vira no motor |
|---|---|---|---|
| `receita` | `cortai/1` (ou `corta/1`, nome antigo) + nome do tipo de edição | — | se a versão for maior que 1, diga para atualizar o plugin (`claude plugin update cortai@cortai`) |
| `tipo` | `editar`, `cortes`, `animacao` | `editar` (ou `cortes` se `formato: cortes`) | escolhe o fluxo (SKILL.md, passo 2) |
| `formato` | `9:16`, `4:5`, `1:1`, `16:9`, `original`, `cortes` | `original` | `montar --formato` (cortes: fluxo de cortes, sempre 9:16) |
| `limpeza.silencio` | `rapido`, `natural`, `nao` | `rapido` | `preparar --ritmo` (nao: não monta, só legenda) |
| `limpeza.erros-de-fala` | `sim`, `nao` | `sim` | transcrever + trechos + takes.json |
| `limpeza.voz` | `leve`, `forte`, `nao` | o do perfil | `preparar --voz` (forte só se instalada; senão use leve e avise) |
| `legenda` | nome de estilo (`corta estilos`), `automatico` ou `nenhuma` | `creator-bold` | `legendar --estilo` (automatico: automatico-e-lote.md) |
| `legenda.ajustes` | `chave=valor` | — | `legendar --ajuste chave=valor` (um por ajuste) |
| `movimento.zoom` | `nao`, `leve`, `normal`, `forte` | `nao` | `montar --zoom` |
| `movimento.enquadrar` | `rosto`, `centro`, `desfocado`, `tela-camera`, `camera` (só a câmera de uma gravação de tela) | `rosto` | `montar --enquadrar` |
| `movimento.efeitos` | `nao`, `automatico`, ou lista de tipos (`palavra-gigante, contador, atras, imagem`) | `nao` | `legendar --efeitos` (ver motion-e-trilha.md). Na lista, `atras` = 1–2 palavras gigantes atrás da pessoa; `imagem` = fotos da pasta |
| `acabamento.gancho` | `sugerir`, `"texto"`, `nao` | `nao` | `legendar --gancho` |
| `acabamento.cta` | `sugerir`, `"texto"`, `nao` | `nao` | `legendar --cta` + `--cta-em` |
| `acabamento.barra` | `sim`, `nao` | `nao` | `legendar --barra` |
| `acabamento.sons` | `nao`, `poucos`, `todos` | `nao` | `legendar --sons` |
| `acabamento.trilha` | `nao`, `automatico`, um estilo, `arquivo` (a música que está na pasta) ou `arquivo=<caminho>` | `nao` | `legendar --trilha` / `--trilha-arquivo` |
| `cortes` | `quantidade=N · duracao=25-60` | `quantidade=5 · duracao=25-90` | só no formato cortes |
| `aprovacao` | `conteudo`, `etapa`, `direto` | `conteudo` | ver abaixo |
| `idioma` | `pt`, `en`, `es` | `pt` | `--idioma` |
| `videos` | caminhos | pedir para arrastar | — |
| `pasta` | caminho de uma pasta (ou de um vídeo), colado ao arrastar | pedir para arrastar | 1 vídeo → edição normal; 2+ → `M lote`. Fotos e áudios da pasta viram material (SKILL.md, passo 1) |
| `lote` | `iguais`, `diferentes`, `automatico` | `iguais` | automatico-e-lote.md |
| `especial` | texto livre da pessoa | — | automatico-e-lote.md, "Algo especial" |
| `animacao` | `tema="…"` ou `roteiro="…"` · `duracao=30` | — | so-animacao.md |
| `voz` | `elevenlabs=<nome>`, `elevenlabs`, `audio` (o áudio que está na pasta) ou `audio="<arquivo>"` | — | só animação: `M narracao` |
| `movimento.enquadrar` (cortes) | também `automatico` | `rosto` | cortes.md, passo 5 |
| `cortes.quantidade` | número ou `automatico` | `5` | cortes.md, passo 3 |

## Aprovação
- `conteudo` (padrão): pare para a pessoa aprovar **takes**, **lista de cortes**, **gancho/CTA** e a
  **prévia da legenda**. O resto segue sozinho.
- `etapa`: pare também depois de cada etapa (silêncio, montagem, legenda) mostrando o resultado.
- `direto`: decida tudo pelos critérios das referências e só mostre no fim, com a lista do que decidiu.

## gancho=sugerir / cta=sugerir
Leia o texto do vídeo e proponha 2–3 opções curtas (gancho: até ~10 palavras, fala com quem assiste e
complementa — não repete — a primeira frase; formato `pergunta | resposta` dá 2 níveis). CTA de anúncio
no Meta: "Toque em Saiba mais" (o link é o botão, nunca "link na descrição"). O `--cta-em` é o segundo
em que a fala da chamada começa (ache na transcrição); sem fala de chamada, use o padrão (4 s antes do fim).
