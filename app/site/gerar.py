"""Gera public/index.html (página completa para o Cloudflare) a partir de ../index.html (versão artifact).
Uso: python3 gerar.py && npx wrangler@4.20.0 deploy"""
from pathlib import Path

aqui = Path(__file__).parent
s = (aqui.parent / "index.html").read_text()
i = s.find("</style>") + len("</style>")
cabeca = s[:i].replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
html = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n' + cabeca +
        '\n<meta name="description" content="Cortaí: edição, cortes e viralização com IA no Claude Code.">\n'
        '</head>\n<body>\n' + s[i:] + '\n</body>\n</html>\n')
(aqui / "public" / "index.html").write_text(html)
print("public/index.html gerado")
