---
name: instalar
description: >-
  Prepara o computador para o Cortaí (Mac ou Windows) — instala o uv, o ffmpeg, as bibliotecas do motor e a parte de animação (Node + Remotion) sem pedir senha de administrador, mede o computador e edita um vídeo de amostra para confirmar que tudo funciona. Use logo depois de instalar ou atualizar o plugin cortai, quando a pessoa pedir para instalar/reinstalar o Cortaí, ou quando o diagnóstico mandar reinstalar.
---

# Cortaí — instalar neste computador

A pasta do plugin é a pasta **duas acima desta skill** (o "Base directory" desta skill termina em
`skills/instalar`). Chame-a de `<PLUGIN>`.

## Passos
1. Diga à pessoa, em uma frase, o que vai acontecer: baixa o que falta (uv, ffmpeg, bibliotecas, a parte de
   animação e o modelo de transcrição: 2–4 GB na primeira vez), mede o computador e edita um vídeo de teste.
   Leva de 10 a 25 minutos dependendo da internet. Não pede senha. Peça para deixar o computador na tomada.
2. Veja o sistema com `uname -s` (no Windows o Bash do Claude Code mostra algo como `MINGW64_NT…`).
3. Rode o instalador **em segundo plano** e acompanhe a saída até o fim:
   - Mac/Linux: `bash "<PLUGIN>/instalar.sh"`
   - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "<PLUGIN>/instalar.ps1")"`
   Se a pessoa pediu a **limpeza de voz forte** (IA, ~2 GB a mais), rode com `CORTA_FORTE=1` antes do comando
   (Windows: `CORTA_FORTE=1 powershell …`). Computador com pouco espaço e sem interesse em animações:
   `CORTA_SEM_MOTION=1` pula a parte de animação (~600 MB); dá para instalar depois rodando de novo.
4. Conte o progresso pelas etapas `== 1/6 … 6/6` (uv, ffmpeg, bibliotecas, animação, medir o computador,
   vídeo de teste). Só diga que terminou quando aparecer
   **"✅ TUDO CERTO"**.
5. Se falhar:
   - leia a mensagem com ❌ — ela já diz o que fazer; explique em português simples;
   - internet caiu: rode de novo (o que já baixou não baixa outra vez);
   - qualquer outra coisa: rode `"<PLUGIN>/bin/corta" diagnostico` e siga a skill `/cortai:diagnostico`.
6. No fim diga:
   - que o Cortaí está pronto **neste computador**;
   - para editar é só colar uma receita do app Cortaí (ou pedir "edita esse vídeo com o Cortaí" e arrastar
     o vídeo);
   - se o plugin acabou de ser instalado nesta conversa, feche e abra o Claude Code uma vez para os
     comandos `/cortai:…` aparecerem.

## Detalhes que a pessoa pode perguntar
- O que fica onde: `uv` em `~/.local/bin`; ffmpeg (só se faltava) em `~/.corta/bin`; bibliotecas dentro da
  pasta do plugin; modelo de transcrição no cache do Hugging Face (`~/.cache/huggingface`).
- Para desinstalar: `claude plugin uninstall cortai@cortai` e apagar a pasta `~/.corta`.
- Mac sem as ferramentas de desenvolvedor pode abrir uma janela pedindo para instalar o git: clique em
  Instalar e rode de novo.
- Voz de IA (ElevenLabs, opcional, para Só animação): a pessoa conecta a chave **no Terminal** (Mac:
  `~/.corta/bin/corta chave elevenlabs`; Windows PowerShell: `& "$env:USERPROFILE\.corta\bin\corta.cmd" chave elevenlabs`).
  Nunca peça a chave na conversa.
