# fromtool.py — extrai o texto devolvido pelo navegador de um arquivo de resultado de ferramenta salvo pelo harness.
# uso: python3 -I fromtool.py <arquivo_tool-results.txt> <saida> [--raw]
# O JS deve devolver 'X'.repeat(20000)+'@@'+TEXTO (o enchimento força o harness a salvar em arquivo).
# Limite da ponte: ~250 mil caracteres por chamada; para textos maiores, devolva pedaços e use --raw (concatenar depois).
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
t = d[0]['text']; t = t[:t.rfind('\n\n(captured')]
if 'truncated: content too large' in t: sys.exit('ERRO: resposta truncada pela ponte; use pedaços menores')
s = json.loads(t)
s = s[s.index('@@') + 2:] if '@@' in s else s
if '--raw' not in sys.argv: json.loads(s)
open(sys.argv[2], 'w', encoding='utf-8').write(s)
print(len(s), 'caracteres ok')
