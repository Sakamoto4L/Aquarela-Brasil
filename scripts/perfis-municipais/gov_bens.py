# gov_bens.py — acrescenta o histórico de bens declarados ao TSE (2006–2026) aos perfis da aba Governo (data/perfis.json).
import json, csv, sys, collections
csv.field_size_limit(10**8)
import bens_all
SC = '/tmp/claude-0/-home-claude/09aefdc5-706f-5d9c-918a-28b3af6171a1/scratchpad'
PFP = f'{SC}/site/data/perfis.json'
PF = json.load(open(PFP)); PERF = PF['perf']
H = json.load(open(f'{SC}/gov/hist.json'))
CG = {'PREFEITO': 'Prefeito', 'VICE-PREFEITO': 'Vice-prefeito', 'VEREADOR': 'Vereador', 'DEPUTADO ESTADUAL': 'Deputado estadual', 'DEPUTADO FEDERAL': 'Deputado federal',
      'DEPUTADO DISTRITAL': 'Deputado distrital', 'SENADOR': 'Senador', 'GOVERNADOR': 'Governador', 'VICE-GOVERNADOR': 'Vice-governador', 'PRESIDENTE': 'Presidente',
      'VICE-PRESIDENTE': 'Vice-presidente', '1º SUPLENTE': '1º suplente de senador', '2º SUPLENTE': '2º suplente de senador'}
# SG_UE de cada candidatura (o SQ de 2006 e 2008 só é único dentro da UE)
want = collections.defaultdict(set)
for k, L in H.items():
    for e in L:
        if e['ano'] >= 2006: want[e['ano']].add(e['sq'])
UE = {}
for y, sqs in want.items():
    for r in csv.DictReader(open(f'{SC}/gov/tse/consulta_cand_{y}_BRASIL.csv', encoding='latin1'), delimiter=';'):
        if r['SQ_CANDIDATO'] in sqs: UE.setdefault((y, r['SQ_CANDIDATO'], r['SG_UF'], r['NR_CANDIDATO']), r['SG_UE'])
need = set(); rows = {}
for k, L in H.items():
    if k not in PERF: continue
    out = []
    for e in L:
        if e['ano'] < 2006: continue
        ue = UE.get((e['ano'], e['sq'], e['uf'], e['num']))
        if not ue: continue
        need.add((e['ano'], ue, e['sq'])); out.append((e['ano'], ue, e['sq'], CG.get(e['cargo'], e['cargo'].capitalize())))
    rows[k] = out
BY = bens_all.load(need)
n = 0
for k, out in rows.items():
    seen = set(); B = []
    for y, ue, sq, cg in out:
        if (y, cg) in seen: continue
        seen.add((y, cg)); b = BY.get((y, ue, sq))
        if b is not None: B.append([y, cg] + b)
    if B: PERF[k]['bens'] = B; n += 1
    else: PERF[k].pop('bens', None)
json.dump(PF, open(PFP, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(n, 'perfis com bens', file=sys.stderr)
