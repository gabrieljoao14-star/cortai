# Modo automático, vários vídeos e "algo especial"

`M` = `"<PLUGIN>/bin/corta"`.

## Automático (`legenda: automatico`, `efeitos=automatico`, `trilha=automatico`)
Depois de transcrever, leia o texto e decida o **nicho e o tom**. Escolha pela tabela, diga a escolha em uma
linha ("Nicho: saúde, tom sério → legenda faixa-de-fundo, trilha emocional, 3 efeitos") e siga.

| Nicho / tom | Legenda | Destaque | Trilha | Efeitos que combinam |
|---|---|---|---|---|
| Jurídico, saúde, finanças, B2B (autoridade) | `faixa-de-fundo`, `karaoke` ou `editorial` | `#FFE14D` | emocional / corporativo | contador, lista, nome-cargo. Sem emoji |
| Vendas, infoproduto, dicas rápidas | `creator-bold` ou `hierarquia` | `#FFE14D` | energia | palavra-gigante, contador, emoji (pouco) |
| Depoimento, história pessoal | `karaoke` ou `maquina-de-escrever` | `#FFFFFF` + palavra `#FFE14D` | emocional | nome-cargo, palavra-gigante (1×) |
| Fitness, esporte | `creator-bold` | `#B6FF3B` | energia | contador, palavra-gigante |
| Tech, apps, games | `neon` | `#3BE8FF` | energia | grafico, seta-circulo, imagem (print) |
| Lifestyle, beleza, rotina | `com-emoji`, `editorial` ou `minimal` | `#FF7AB6` | lofi | emoji, imagem |
| Humor, entretenimento | `cartoon` ou `com-emoji` | `#FFE14D` | energia | emoji, palavra-gigante |
| Aula, tutorial, explicação | `karaoke` (curto) / `classica` (longo) | `#FFE14D` | lofi / corporativo / nenhuma em aula longa | lista, seta-circulo, grafico |
| Alerta, golpe, prazo | `creator-bold` | `#FF4D4D` | tensao | palavra-gigante, manchetes (só reais) |

- Se a pessoa tem cor de marca (na receita, no logo da pasta ou na roupa/cenário do vídeo), use a cor dela
  como destaque.
- `efeitos=automatico`: siga a densidade de motion-e-trilha.md (1 a cada ~8–12 s; 2–3 momentos grandes por
  minuto) e só onde a fala pede. Na dúvida, **menos**.
- `gancho=sugerir` no automático com `aprovacao: direto`: escolha você a melhor opção.

## Vários vídeos (`pasta:` na receita)
Todos os vídeos da pasta (o motor pula os que já são saída do Cortaí). Fotos e logos da pasta são material
para o "algo especial" e para o efeito `imagem`.

1. `M lote "<pasta>" --voz <voz> --ritmo <ritmo>` **em segundo plano** (ver video-falado.md, "Vários vídeos").
2. Decida o acabamento de cada um pelo modo `lote:` da receita:

| `lote:` | Faz | Nome da saída |
|---|---|---|
| `iguais` (padrão) | a mesma receita em todos | `<nome> (legendado).mp4` |
| `diferentes` | **para testar anúncio**: cada vídeo ganha uma combinação diferente (estilo de legenda + cor + trilha + gancho). Limpeza e corte iguais em todos, para a comparação ser justa | `<nome> (A).mp4`, `(B)`, … |
| `automatico` | cada vídeo decide sozinho pelo nicho/tom do próprio texto (tabela acima) | `<nome> (legendado).mp4` |

- `diferentes`: tire as combinações das 2–3 linhas da tabela que servem ao nicho (não misture nicho sério com
  `cartoon`). No fim entregue uma tabela "vídeo → legenda, cor, trilha, gancho" para a pessoa comparar os
  resultados do anúncio.
- Uma aprovação só para todos: mostre os takes e os ganchos de todos juntos.
- Monte e legende um vídeo por vez (dois ao mesmo tempo fica mais lento).

**Economia (diga isso à pessoa no fim):** cada lote numa **conversa nova** do Claude Code. Conversa longa
gasta mais e fica mais lenta; os dados ficam em `_corta`, então ajuste depois também funciona numa conversa
nova ("ajuste a legenda do vídeo X da pasta Y").

## "Algo especial nesse vídeo" (`especial: "…"`)
Leia **antes de começar**: é o pedido da pessoa e vale mais que o padrão da receita.
- Cita arquivo da pasta (foto de produto, print, logo) → efeito `imagem` com `"arquivo"` no segundo em que
  a pessoa fala daquilo.
- Nome próprio, marca, termo técnico → use a grafia certa no `corrigir` e no texto dos efeitos.
- "Não corte a parte X", "comece em Y" → respeite nos takes/cortes.
- Pedido que o motor não faz (ex.: trocar o fundo, tirar objeto do vídeo): diga com honestidade que ainda
  não dá e ofereça o mais perto possível. Nunca finja que fez.
