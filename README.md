# Cortaí

**Edição, cortes e viralização com IA, dentro do Claude Code.**

Você escolhe a edição no app **https://cortai.dvbusiness.online**, copia a receita, cola no Claude Code e
arrasta a pasta com os vídeos. O Cortaí:

- tira os silêncios e os erros de fala (fica só o melhor take);
- legenda em 13 estilos (Creator bold, Karaokê, Hierarquia, Máquina de escrever, Com emoji…);
- dá zoom no rosto e enquadra para Reels, TikTok, Shorts, Feed ou YouTube;
- transforma live, aula ou podcast em vários cortes curtos (acha os melhores trechos sozinho);
- põe animações (palavra gigante, atrás da pessoa, números, listas, gráficos, foto do produto);
- coloca gancho, chamada no final, sons e trilha sonora que abaixa quando a pessoa fala;
- faz vídeos só de animação, com a sua voz gravada ou voz de IA (ElevenLabs);
- edita vários vídeos de uma vez (todos iguais, cada um diferente para teste de anúncio, ou automático);
- confere o próprio resultado antes de entregar.

Funciona no **Mac** (chip Apple ou Intel) e no **Windows 10/11**. Tudo roda no seu computador.

## Instalar (uma vez por computador)
Precisa: Claude Code com plano pago, internet e uns 10 GB livres. Deixe o computador na tomada.
Cole isto no Claude Code:

```
Instale o Cortaí para mim, sem pular nenhum passo e me mostrando o progresso:
1. Rode no terminal: claude plugin marketplace add gabrieljoao14-star/cortai
   (se disser que já existe, rode: claude plugin marketplace update cortai)
2. Rode: claude plugin install cortai@cortai
3. Descubra a pasta do plugin com: claude plugin list --json (o caminho de instalação do "cortai").
4. Rode o instalador dessa pasta em segundo plano e acompanhe até o fim:
   no Mac: bash "<pasta>/instalar.sh"
   no Windows: powershell -NoProfile -ExecutionPolicy Bypass -File "<pasta>\instalar.ps1"
   Ele baixa o que falta (2 a 4 GB, de 10 a 25 minutos) e edita um vídeo de teste.
   Me lembre de deixar o computador na tomada.
5. Só termine quando aparecer "✅ TUDO CERTO". Se der erro, me explique em português simples o que fazer.
6. No fim, me peça para fechar e abrir o Claude Code.
```

## Usar
1. Abra **https://cortai.dvbusiness.online**, escolha a edição e toque em **Copiar receita**.
2. Crie uma pasta no computador e coloque o vídeo (ou os vídeos) dentro. Fotos do produto, logo, música
   ou a sua voz gravada também vão nessa pasta.
3. Abra uma **conversa nova** no Claude Code e cole a receita.
4. **Arraste a pasta** para a conversa, logo depois do texto, e aperte Enter.

Uma pasta por conversa (mais rápido e gasta menos). Uma edição por vez no mesmo computador.
Se algo der errado: digite `/cortai:diagnostico`.

Voz de IA (opcional): crie a chave em elevenlabs.io e conecte no Terminal (Mac)
`~/.corta/bin/corta chave elevenlabs` ou no PowerShell (Windows)
`& "$env:USERPROFILE\.corta\bin\corta.cmd" chave elevenlabs`. A chave fica só no seu computador.

## Atualizar
```
Atualize o Cortaí para mim:
1. Rode: claude plugin marketplace update cortai
2. Rode: claude plugin update cortai@cortai
3. Descubra a pasta nova com: claude plugin list --json e rode o instalador dela de novo, em segundo plano,
   até aparecer "✅ TUDO CERTO".
4. No fim, me peça para fechar e abrir o Claude Code.
```

## O que tem aqui
| Pasta | O que é |
|---|---|
| `plugins/cortai/skills` | Skills do Claude Code: `editar` (lê a receita e conduz), `instalar`, `diagnostico`. |
| `plugins/cortai/motor` | Motor de edição em Python (`corta preparar`, `montar`, `legendar`, `cortar`, `animacao`, `verificar`…). |
| `plugins/cortai/motion` | Animações em Remotion (efeitos e Só animação). |
| `plugins/cortai/bin/corta` | Lançador do motor (acha o `uv` e usa as versões travadas). |
| `plugins/cortai/instalar.sh` / `instalar.ps1` | Instaladores do Mac e do Windows (sem senha de administrador). |
| `plugins/cortai/catalogo/legendas` | Estilos de legenda (um arquivo por estilo). |
| `plugins/cortai/assets` | Fontes OFL, emoji Noto (Apache 2.0), detector de rosto YuNet (MIT), recorte MODNet (Apache 2.0), soundfont GeneralUser GS e o vídeo de amostra. Licenças junto de cada arquivo. |
| `app` | O app web (receitas). |
| `.github/workflows` | Teste automático no Mac e no Windows a cada mudança, incluindo os instaladores do zero. |
