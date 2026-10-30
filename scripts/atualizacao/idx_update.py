# idx_update.py — atualiza a aba Índices do Aquarela Brasil só com o que mudou.
# uso: python3 -I idx_update.py <index.html> <pasta_com_bcb.json_focus.json_sidra.json_ipea.json>
# Reescreve o HTML no lugar (const D = {...}; e a data do rodapé) e imprime um resumo das mudanças.
import json, re, sys, datetime, os
from decimal import Decimal, ROUND_HALF_UP
try:
    from zoneinfo import ZoneInfo
    HOJE = datetime.datetime.now(ZoneInfo('America/Sao_Paulo')).date()
except Exception:
    HOJE = datetime.date.today()
HTML, IN = sys.argv[1], sys.argv[2]
if len(sys.argv) > 3: HOJE = datetime.date.fromisoformat(sys.argv[3])
Y = HOJE.year
ld = lambda f: json.load(open(os.path.join(IN, f)))
BCB, FOC, SID, IPE = ld('bcb.json'), ld('focus.json'), ld('sidra.json'), ld('ipea.json')
MES = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']
MAB = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']
POP = {2020:209164889,2021:210103642,2022:210862983,2023:211695158,2024:212583750,2025:213421037,2026:214211951,2027:214959713,2028:215667282,2029:216337693,2030:216973093,2031:217562970,2032:218096284,2033:218574144,2034:218997707,2035:219367247,2036:219681891,2037:219940741,2038:220144140,2039:220292836,2040:220386440,2041:220425299,2042:220410205,2043:220341694,2044:220220282,2045:220045691}
def R(x, n=1):
    if x is None: return None
    q = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
    return float(q) if n > 0 else int(q)
def br(x, n=1):
    s = f'{abs(x):,.{n}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return ('-' if x < 0 else '') + s
def dlong(d, ano=True):  # 'dd/mm/aaaa'
    dd, mm, yy = d.split('/'); return f"{int(dd)}{'º' if dd=='01' else ''} de {MES[int(mm)-1]}" + (f' de {yy}' if ano else '')
def mesano(d): dd, mm, yy = d.split('/'); return f'{MES[int(mm)-1]} de {yy}'
def todate(d): dd, mm, yy = d.split('/'); return datetime.date(int(yy), int(mm), int(dd))

src = open(HTML, encoding='utf-8').read()
m = re.search(r'^const D = (\{.*\});$', src, re.M)
D = json.loads(m.group(1))
OLD = json.loads(m.group(1))
# ---- garante que todas as séries cheguem até o ano corrente
for k, S in D.items():
    if isinstance(S, dict) and 'start' in S and 'v' in S:
        n = Y - S['start'] + 1
        for f in ('v', 'extra', 'points'):
            if f in S and len(S[f]) < n: S[f] += [None] * (n - len(S[f]))
def put(k, y, v):
    S = D[k]; S['v'][y - S['start']] = v
def get(k, y):
    S = D[k]; i = y - S['start']; return S['v'][i] if 0 <= i < len(S['v']) else None
def putx(k, y, v):
    S = D[k]; S.setdefault('extra', [None] * len(S['v'])); S['extra'][y - S['start']] = v
OV = {}; V = dict(D.get('_v', {}))
def tail(i, y, t, tag=None):
    o = OV.setdefault(i, {'tail': {}}); o['tail'][str(y)] = t
    if tag is not None: o['tag'] = tag
for i in ('pib','pib-por-pessoa','inflacao','selic','dolar','salario-minimo','divida-liquida','divida-bruta','resultado-primario','juros-reais','reservas','divida-externa'):
    OV.setdefault(i, {'tail': {}})
def boletim(data_iso):
    d = datetime.date.fromisoformat(data_iso)
    if d.weekday() == 4: d += datetime.timedelta(days=3)
    return d.strftime('%d/%m/%Y')
anos = [Y - 1, Y]
# ---- Selic e meta
meta = [(todate(d), float(v)) for d, v in BCB['meta']]
def meta_em(dt):
    v = None
    for d, x in meta:
        if d <= dt: v = x
    return v
cur_meta = meta_em(HOJE); cur_desde = max(d for d, x in meta if d <= HOJE)
partial = {}
for y in anos:
    s = BCB['selic'].get(str(y))
    if not s: continue
    last = todate(s['last']); full = y < Y and last.month == 12 and last.day >= 28
    if full: put('selic', y, R(s['acc'], 2)); partial[('selic', y)] = False
    else:
        ann = ((1 + s['acc'] / 100) ** (252 / s['n']) - 1) * 100
        put('selic', y, R(ann, 2)); partial[('selic', y)] = True
        md = meta_em(min(HOJE, datetime.date(y, 12, 31)))
        tail('selic', y, f"Parcial: {br(R(s['acc'],2),2)}% acumulados de {dlong(s['first'],False)} a {dlong(s['last'],False)}, o equivalente a {br(R(ann,2),2)}% em um ano. Meta atual: {br(md,2).rstrip('0').rstrip(',')}% (Copom, {MAB[cur_desde.month-1]}/{cur_desde.year})")
    putx('selic', y, meta_em(min(HOJE, datetime.date(y, 12, 31))))
pk = max(x for d, x in meta if d >= HOJE.replace(year=HOJE.year - 3))
mt = lambda x: br(x, 2).rstrip('0').rstrip(',')
if cur_meta == pk:
    V['selic_meta_txt'] = f'Está em <b>{mt(cur_meta)}%</b> desde {MES[cur_desde.month-1]} de {cur_desde.year}.'
else:
    i0 = max(j for j, (d, x) in enumerate(meta) if x == pk); a = meta[i0][0]; b = meta[i0 + 1][0]
    V['selic_meta_txt'] = f'Ficou em <b>{mt(pk)}%</b> de {MES[a.month-1]} de {a.year} a {MES[b.month-1]} de {b.year} e está em <b>{mt(cur_meta)}%</b> desde {MES[cur_desde.month-1]} de {cur_desde.year}.'
# ---- Dólar
for y in anos:
    s = BCB['dol'].get(str(y))
    if not s: continue
    put('dol', y, R(s['avg'], 3)); last = todate(s['last'])
    if not (y < Y and last.month == 12 and last.day >= 28):
        tail('dolar', y, f"Média dos dias úteis de {dlong(s['first'],False)} a {dlong(s['last'])}")
dm = {k: v for k, v in D['dolm']}
for k, (avg, n) in BCB['dolm'].items(): dm[k] = R(avg, 4)
D['dolm'] = sorted([[k, v] for k, v in dm.items()])
# ---- IPCA
num = lambda x: x not in (None, '...', '-', 'X', '..')
ip = SID['ipca']; acc = {k: v for k, v in ip['69'].items() if num(v)}; nidx = {k: v for k, v in ip['2266'].items() if num(v)}
src_ipca = {}
for y in anos:
    if f'{y}12' in acc:
        put('ipca', y, R(float(acc[f'{y}12']), 2)); src_ipca[y] = 'ibge'
    else:
        f = FOC.get(f'IPCA|{y}')
        if not f: continue
        put('ipca', y, R(f['Mediana'], 2)); src_ipca[y] = 'focus'
        ms = sorted(p for p in acc if p.startswith(str(y)))
        t = f"Projeção Focus de {boletim(f['Data'])}"
        if ms:
            p = ms[-1]; p12 = f'{y-1}{p[4:]}'
            t += f". Até {MES[int(p[4:])-1]}: {br(R(float(acc[p]),2),2)}% no ano"
            if p12 in nidx: t += f" e {br(R((float(nidx[p])/float(nidx[p12])-1)*100,2),2)}% em 12 meses"
        tail('inflacao', y, t, 'projeção')
# ---- PIB (Contas Anuais > Trimestrais > Focus)
src_pib = {}
for p, v in SID['cna']['9810'].items():
    if v not in ('...', '-', 'X', None): put('pib', int(p), R(float(v), 1)); src_pib[int(p)] = 'cna'
for y in anos:
    if src_pib.get(y) == 'cna': continue
    q = SID['cnt']['6562'].get(f'{y}04')
    if q not in (None, '...', '-'):
        put('pib', y, R(float(q), 1)); src_pib[y] = 'cnt'
    else:
        f = FOC.get(f'PIB Total|{y}')
        if f:
            put('pib', y, R(f['Mediana'], 1)); src_pib[y] = 'focus'
            tail('pib', y, f"Projeção do mercado (Boletim Focus de {boletim(f['Data'])})", 'projeção')
# ---- PIB por pessoa (reais de 2025), anos >= 2026
for y in range(2026, Y + 1):
    if get('pib', y) is None or get('pc', y - 1) is None or y not in POP: continue
    put('pc', y, R(get('pc', y - 1) * (1 + get('pib', y) / 100) * POP[y - 1] / POP[y], 0))
    if src_pib.get(y) == 'focus':
        tail('pib-por-pessoa', y, f"Estimativa com a projeção Focus para o PIB ({br(get('pib',y),1)}%) e a população estimada pelo IBGE para {y}", 'estimativa')
    elif src_pib.get(y) == 'cnt':
        tail('pib-por-pessoa', y, f'Estimativa com o PIB das Contas Trimestrais ({br(get("pib",y),1)}%) e a população estimada pelo IBGE para {y}', 'estimativa')
# ---- Juros reais
for y in anos:
    s, i = get('selic', y), get('ipca', y)
    if s is None or i is None: continue
    put('jr', y, R(((1 + s / 100) / (1 + i / 100) - 1) * 100, 2))
    ps, pi = partial.get(('selic', y)), src_ipca.get(y) == 'focus'
    if ps or pi:
        t = 'Parcial: ' + ' e '.join(x for x in [f'Selic de {y} anualizada' if ps else '', 'IPCA projetado pelo Focus' if pi else ''] if x)
        tail('juros-reais', y, t, 'parcial')
# ---- Salário mínimo real (Ipeadata, INPC) e nominal de dezembro
for y, (avg, n, lastm) in IPE['real'].items():
    if int(y) >= D['sm']['start']: put('sm', int(y), R(avg, 0))
nom = {int(y): v for y, v in IPE['nom'].items()}
for y in range(1995, Y + 1):
    if y in nom: putx('sm', y, R(nom[y], 0))
lastd = max(v[2] for v in IPE['real'].values()); ly, lm = int(lastd[:4]), int(lastd[5:7])
V['sm_ref'] = f'{MES[lm-1]} de {ly}'
OV['salario-minimo']['sub'] = 'Média do ano, corrigida pela inflação, em reais de {{sm_ref}}'
if lm < 12: tail('salario-minimo', ly, f'Média de janeiro a {MES[lm-1]} de {ly}')
v61 = get('sm', 1961); sup = next((y for y in range(1962, ly + 1) if (get('sm', y) or 0) > v61), None)
vly = get('sm', ly); maior = vly >= max(x for x in D['sm']['v'] if x is not None)
V['sm_txt'] = (f"O poder de compra de 1961 (<b>R$ {br(v61,0)}</b> de hoje) " + (f'só foi superado em {sup}; ' if sup else 'ainda não foi superado; ') +
               f"em {ly} a média {'está' if lm < 12 else 'ficou'} em <b>R$ {br(vly,0)}</b>{', a maior da série' if maior else ''}, com o mínimo nominal de <b>R$ {br(nom.get(ly, 0),0)}</b>.")
# ---- Dívidas e primário (BCB mensal)
def mensal(cod, key, oid, neg, fmt_tail, fmt_tag):
    serie = [(todate(d), float(v)) for d, v in BCB['mens'][cod]]
    for y in anos:
        ms = [(d, v) for d, v in serie if d.year == y]
        if not ms: continue
        d, v = ms[-1]; val = R(-v if neg else v, 1); put(key, y, val)
        if d.month != 12: tail(oid, y, fmt_tail(d), fmt_tag(d))
    return serie[-1]
d, v = mensal('4513', 'dlsp', 'divida-liquida', False, lambda d: f'Posição de {MES[d.month-1]} de {d.year}', lambda d: MES[d.month-1])
V['dlsp_txt'] = f'; em {MES[d.month-1]} de {d.year} estava em {br(R(v,1),1)}%.' if d.month != 12 else '.'
d, v = mensal('13762', 'dbgg', 'divida-bruta', False, lambda d: f'Posição de {MES[d.month-1]} de {d.year}', lambda d: MES[d.month-1])
V['dbgg_txt'] = f'; em {MES[d.month-1]} de {d.year}, {br(R(v,1),1)}%.' if d.month != 12 else '.'
# ---- Reservas internacionais (SGS 3546, US$ milhões, mensal) e dívida externa (Ipeadata BM_DEXTEI, anual)
if '3546' in BCB['mens'] and 'res' in D:
    sr = [(todate(d), float(v)) for d, v in BCB['mens']['3546']]
    for y in anos:
        ms = [(d, v) for d, v in sr if d.year == y]
        if not ms: continue
        d, v = ms[-1]; put('res', y, R(v / 1000, 1))
        if 'dext' in D and y >= D['dext']['start'] and d.month == 12: putx('dext', y, R(v / 1000, 1))
        if d.month != 12: tail('reservas', y, f'Posição de {MES[d.month-1]} de {d.year}', MES[d.month-1])
    d, v = sr[-1]
    V['res_txt'] = f'Em {MES[d.month-1]} de {d.year} estavam em US$ {br(R(v/1000,1),1)} bilhões.' if d.month != 12 else ''
if 'dext' in IPE and 'dext' in D:
    for y, v in IPE['dext'].items():
        if int(y) >= D['dext']['start'] and v is not None: put('dext', int(y), R(v / 1000, 1))
mensal('5793', 'prim', 'resultado-primario', True, lambda d: f'Acumulado em 12 meses até {MES[d.month-1]} de {d.year}', lambda d: f'12 meses até {MAB[d.month-1]}')
# ---- Séries anuais da PNAD Contínua
for key, tab, var in (('des', 'desA', '4099'), ('inf', 'infA', '12466'), ('gini', 'gini', '10681')):
    for p, v in SID[tab][var].items():
        if v not in ('...', '-', 'X', None) and int(p) >= D[key]['start']: put(key, int(p), R(float(v), 3 if key == 'gini' else 1))
for p, v in SID['analf']['10267'].items():
    if v not in ('...', '-', 'X', None): putx('analf', int(p), R(float(v), 1))
dmq = {k: v for k, v in SID['desM']['4099'].items() if num(v)}; p = max(dmq); y, mm = int(p[:4]), int(p[4:])
m0 = (mm - 3) % 12 + 1; y0 = y if mm >= 3 else y - 1
ini = f'{MES[m0-1]}' + (f' de {y0}' if y0 != y else '')
t = f'No trimestre de {ini} a {MES[mm-1]} de {y} ficou em <b>{br(R(float(dmq[p]),1),1)}%</b>'
p12 = f'{y-1}{p[4:]}'
if p12 in dmq: t += f', contra {br(R(float(dmq[p12]),1),1)}% um ano antes'
t += '.'
la = max(int(k) for k, v in SID['desA']['4099'].items() if v not in ('...', '-', None))
if la < y: t += f' A taxa anual de {la+1} sai em janeiro de {la+2}.'
V['des_tri_txt'] = t
# ---- KPIs do topo
def last_final(key, fonte):
    return max(y for y in range(Y - 3, Y + 1) if get(key, y) is not None and fonte.get(y) != 'focus')
lp = last_final('pib', src_pib); li = last_final('ipca', src_ipca); lx = max(y for y in range(Y - 3, Y + 1) if get('des', y) is not None)
sg = lambda x: ('+' if x > 0 else '') + br(x, 1)
D['_kpi'] = [[f'PIB {lp}', sg(get('pib', lp)) + '%', '', f'O PIB de {lp+1} será divulgado pelo IBGE em março de {lp+2}.'],
             [f'Inflação {li}', br(get('ipca', li), 2) + '%', '', f'O IPCA de {li+1} será divulgado pelo IBGE em janeiro de {li+2}.'],
             [f'Desemprego {lx}', br(get('des', lx), 1) + '%', '', f'A taxa média de desemprego de {lx+1} será divulgada pelo IBGE no fim de janeiro de {lx+2}.'],
             ['Selic hoje', mt(cur_meta) + '%', '', '']]
V['atualizado'] = HOJE.strftime('%d/%m/%Y')
D['_v'] = V; D['_ov'] = OV; D['_end'] = Y
# ---- grava
src = src[:m.start(1)] + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + src[m.end(1):]
src = re.sub(r'(<span id="footSrc">[^<]*?atualizado em )\d{2}/\d{2}/\d{4}', lambda mm: mm.group(1) + HOJE.strftime('%d/%m/%Y'), src, count=1)
open(HTML, 'w', encoding='utf-8').write(src)
# ---- resumo
mud = []
for k, S in D.items():
    if not (isinstance(S, dict) and 'v' in S): continue
    O = OLD.get(k, {})
    for f in ('v', 'extra'):
        a, b = O.get(f) or [], S.get(f) or []
        for i, x in enumerate(b):
            o = a[i] if i < len(a) else None
            if x != o: mud.append(f"{k}{'(extra)' if f=='extra' else ''} {S['start']+i}: {o} → {x}")
if D['dolm'] != OLD.get('dolm'): mud.append('dólar mensal atualizado')
print(json.dumps({'mudancas': mud, 'kpi': D['_kpi']}, ensure_ascii=False, indent=1))
