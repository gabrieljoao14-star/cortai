# Motion (efeitos) e trilha

`M` = `"<PLUGIN>/bin/corta"`. Efeitos e trilha entram no `M legendar` (uma gravação só).

## Efeitos de motion
`M legendar "<editado>.mp4" --estilo … --efeitos "<pasta>/_corta/<nome>/efeitos.json"`

```json
{"efeitos": [
  {"tipo": "emoji",           "em": 18.4, "duracao": 1.8, "props": {"emoji": "⚠️"}},
  {"tipo": "palavra-gigante", "em": 16.7, "duracao": 2.2, "props": {"texto": "em dobro", "subtitulo": "a devolução vem"}},
  {"tipo": "nome-cargo",      "em": 71.7, "duracao": 3.0, "props": {"nome": "Ana Souza", "cargo": "Nutricionista"}},
  {"tipo": "lista",           "em": 93.0, "duracao": 3.5, "props": {"titulo": "Diagnóstico", "itens": ["…", "…", "…"]}},
  {"tipo": "contador",        "em": 40.2, "duracao": 2.5, "props": {"de": 0, "ate": 7000, "prefixo": "R$ ", "rotulo": "por mês"}},
  {"tipo": "grafico",         "em": 55.0, "duracao": 3.0, "props": {"titulo": "Vendas", "barras": [{"rotulo": "Antes", "valor": 30}, {"rotulo": "Depois", "valor": 90}]}},
  {"tipo": "manchetes",       "em": 5.0,  "duracao": 3.5, "props": {"itens": ["…", "…", "…"]}},
  {"tipo": "seta-circulo",    "em": 30.0, "duracao": 2.5, "props": {"alvo": {"x": 0.3, "y": 0.4, "w": 0.4, "h": 0.1}}},
  {"tipo": "imagem",          "em": 12.0, "duracao": 3.0, "props": {"arquivo": "produto.png", "legenda": "MenoPro"}}
]}
```
- `em` = segundo do vídeo **editado** em que a palavra é dita (ache com `M texto "<editado>.mp4"`). O efeito
  mostra o que a pessoa fala, na hora em que fala.
- O motor mede o rosto e põe o efeito no maior espaço livre (acima da cabeça ou entre o queixo e a legenda).
  Imagem que não cabe vai para o lado de quem fala, na altura do peito. Se não couber, vira "momento
  grande" com o fundo escurecido (e a legenda some). Não precisa passar posição.
- Durante palavra gigante, contador, gráfico e manchetes a legenda some de baixo (não aparece texto duplicado).
- `"atras": true` coloca o efeito **atrás da pessoa** (recorte automático de quem fala). Use na palavra gigante
  de 1 palavra curta ("DOBRO", "GRÁTIS"), no máximo 1–2 vezes por vídeo: é o efeito mais marcante do kit.
- A cor segue o destaque da legenda. Primeira vez de um efeito leva ~15 s para renderizar; depois fica em cache.

### Quando usar (e quando não)
| Efeito | Use quando a pessoa… | Não use |
|---|---|---|
| palavra-gigante | diz a palavra-chave da ideia ("dobro", "grátis", "erro") | mais de 2× por minuto |
| contador | fala um número que importa (R$, %, quantidade) | número sem peso |
| lista | enumera ("são 3 coisas…") | lista de 1 item |
| grafico | compara (antes/depois, simples/dobro) | sem números de verdade |
| nome-cargo | se apresenta | depois dos primeiros 20 s, a não ser que seja a apresentação |
| manchetes | "todo mundo está falando de…", notícias | sem manchete real (não invente fato) |
| emoji | alerta, humor, emoção forte | em conteúdo sério a cada frase |
| seta-circulo | aponta algo na tela (documento, produto) | sem algo para apontar |
| imagem | fala do produto, print, resultado que está numa foto da pasta (`arquivo`, caminho relativo ao efeitos.json ou completo). PNG transparente = produto solto com sombra; foto comum = cartão com borda | foto que não é da pessoa/marca (não invente imagem) |

**Densidade:** 1 efeito a cada ~8–12 s em vídeo de até 90 s; no máximo 2–3 "momentos grandes" por minuto.
Nada nos primeiros 1,5 s se tiver gancho (o gancho é o momento). Sons só nas viradas (`--sons poucos`).

Com referência visual na pasta (vídeo ou print de um estilo que a pessoa quer): antes de escrever o
efeitos.json, abra 3–4 quadros dela e anote em 3 linhas a cor de destaque, o peso das letras e o ritmo; use
`--ajuste destaque=#…` e os mesmos tipos de efeito que combinam com esse ritmo.

### Ciclo de crítica (obrigatório quando houver efeito)
1. `M quadros "<final>.mp4" --em <um segundo dentro de cada efeito>` e **abra a imagem**.
2. Dê nota de 1 a 10 em: rosto livre, leitura no celular, texto não duplicado, efeito na palavra certa,
   variedade, excesso (menos é mais).
3. Corrija os 3 piores (tirar efeito, mudar `em`, trocar tipo, encurtar texto) e grave de novo.
4. Repita até tudo ficar 8 ou mais. Só então entregue, dizendo as notas.

## Trilha sonora
`--trilha <estilo>` compõe uma trilha original que segue a edição (entra leve, vácuo antes das viradas,
resolve no CTA) e abaixa sozinha quando a pessoa fala. Música da pessoa: `--trilha-arquivo "<musica.mp3>"`.

| Estilo | Combina com |
|---|---|
| emocional | depoimento, jurídico, saúde, história pessoal |
| corporativo | produto, empresa, tutorial, serviço |
| tensao | alerta, erro, prazo, golpe, polêmica |
| lofi | rotina, estudo, bastidor, lifestyle |
| epico | conquista, lançamento, antes e depois |
| energia | fitness, vendas rápidas, dicas, tech |

`trilha: automatico` na receita = escolha pela tabela, pelo tom do texto. Vídeo de aula longa: sem trilha.
