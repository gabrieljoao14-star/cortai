# Fluxo: vídeo longo (live, aula, podcast) vira vários cortes verticais

`M` = `"<PLUGIN>/bin/corta"`. `V` = caminho do vídeo longo entre aspas.

1. `M preparar V --ritmo natural --voz <voz>` e depois `M transcrever V`.
   Vídeo de 1 h leva ~2 h para transcrever: rode em segundo plano e avise a pessoa do tempo antes.
2. `M texto V` — o texto inteiro em frases com tempo. **Leia tudo**, não só o começo: uma leitura completa
   costuma dar mais de 10 candidatos.
3. Escolha os cortes (critério abaixo), na quantidade e duração da receita (`quantidade=automatico`: todos os
   que passam no critério, normalmente 3–10 por hora de vídeo; nunca encha com corte fraco). Monte a tabela para a pessoa:
   `nº | início–fim | duração | primeira frase | por que funciona | gancho sugerido`, em ordem de força do
   gancho (não cronológica). Espere a aprovação (a pessoa pode trocar, tirar ou ajustar limites).
4. Escreva `<pasta do vídeo>/_corta/<nome>/cortes.json`:
   ```json
   {"cortes": [{"nome": "O prazo que ninguém conta", "inicio": "12:03.4", "fim": "12:58.0",
                "gancho": "O prazo que ninguém conta | e derruba o processo"}]}
   ```
   Limites **exatos pela transcrição**: início da primeira palavra e fim da última da ideia (nunca "de olho").
5. `enquadrar=automatico`: olhe 3 quadros do vídeo (`M quadros V --n 3`). Só a pessoa → `rosto`; tela
   compartilhada com a câmera num canto → `tela-camera`; **tela com dado pessoal (processo, nome de cliente,
   extrato, CPF) ou sem nada útil para quem assiste → `camera`** (só a câmera, sobre ela mesma desfocada;
   nada da tela aparece); 2+ pessoas lado a lado → `centro`. Nunca pinte a tela de preto na mão.
   Gravação com tela + câmera (Zoom, Meet, OBS): `M regioes V`, **abra `regioes.png`** e confira as caixas
   antes de cortar. Se estiverem erradas, escreva as caixas à mão num JSON e passe `--regioes`.
6. `M cortar V --cortes "<…>/cortes.json" --enquadrar <rosto|tela-camera|camera> --zoom <zoom> --legenda <estilo> [--ajuste …] [--cta "…"] [--barra] [--sons poucos] [--trilha <estilo>]`
   Sai `<vídeo> - cortes/01 - nome (final).mp4`. `legenda: automatico` e `trilha=automatico`: escolha pelo
   nicho (automatico-e-lote.md); um estilo só para todos os cortes do mesmo vídeo.
   Efeitos de motion nos cortes (só se a receita pedir): depois do `cortar`, rode
   `M legendar "<vídeo> - cortes/01 - nome.mp4" … --efeitos …` (o corte sem "(final)") com o mesmo estilo,
   gancho e trilha, salvando por cima do nome "(final)" com `--saida`.
7. Abra 1 quadro de 2–3 cortes (prévia rápida: `M previa "<corte>.mp4" --estilo …`) e rode
   `M verificar` em pelo menos 3 cortes. Liste à pessoa o que foi conferido e o que não foi.

## Critério de um bom corte (validado em 11 shorts publicados)
- **Gancho forte nos 3 primeiros segundos**: caso com virada, analogia memorável, afirmação
  contra-intuitiva, aviso de risco/prazo com urgência real, recomendação específica.
- **Se sustenta sozinho**: não depende do slide anterior nem de "como eu falei antes".
- **Fecha uma ideia** e termina no clímax: corte "obrigado", "próximo slide", "vamos para a próxima".
- 25–90 s depois de tirar as pausas (siga a duração da receita).
- Começo limpo: corte "então, deixa eu falar…" do início.
- Tela com dado pessoal (CPF, processo, nome de cliente, endereço): **não use esse trecho** e avise a
  pessoa — o desfoque automático ainda não faz parte do /corta.
