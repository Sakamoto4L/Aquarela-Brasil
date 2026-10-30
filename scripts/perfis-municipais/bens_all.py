# bens_all.py — soma os bens declarados ao TSE por candidatura (ano, SQ_CANDIDATO), de 2006 a 2026.
# Categorias: 0 imóveis · 1 veículos, barcos e aeronaves · 2 dinheiro, contas e aplicações · 3 participação em empresas · 4 outros.
# Em anos em que o TSE não classifica os bens (quase tudo como "outros bens e direitos"), devolve só total e quantidade.
import csv, collections, sys
csv.field_size_limit(10**8)
BENS_DIR = '/tmp/bens'
YEARS = list(range(2006, 2027, 2))
def bcat(c):
    try: c = int(c)
    except ValueError: return 4
    if 1 <= c <= 19: return 0
    if c in (21, 22, 23): return 1
    if 41 <= c <= 79 or c in (95, 97): return 2
    if c in (31, 32, 39): return 3
    return 4
def val(s):
    s = (s or '0').strip()
    if ',' in s: s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except ValueError: return 0.0
def load(need):
    """need: conjunto de (ano, SG_UE, sq) — em 2006 e 2008 o SQ só é único dentro da UE. Devolve {(ano, ue, sq): [total, itens, c0..c4] ou [total, itens]}."""
    out = {}
    for y in YEARS:
        ny = {(ue, sq) for (yy, ue, sq) in need if yy == y}
        if not ny: continue
        acc = collections.defaultdict(lambda: [0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0]); n99 = nall = 0
        for r in csv.DictReader(open(f'{BENS_DIR}/bem_candidato_{y}_BRASIL.csv', encoding='latin1'), delimiter=';'):
            nall += 1; c = r['CD_TIPO_BEM_CANDIDATO']; n99 += c == '99'
            sq = (r['SG_UE'], r['SQ_CANDIDATO'])
            if sq not in ny: continue
            v = val(r['VR_BEM_CANDIDATO']); b = acc[sq]; b[0] += v; b[1] += 1; b[2 + bcat(c)] += v
        cat = n99 / max(nall, 1) < .9
        for sq in ny:
            b = acc.get(sq)
            if not b: out[(y,) + sq] = [0, 0]; continue
            out[(y,) + sq] = [round(b[0]), b[1]] + ([round(x) for x in b[2:]] if cat else [])
        print('bens', y, len(ny), 'candidaturas;', 'com categorias' if cat else 'sem categorias', file=sys.stderr)
    return out
