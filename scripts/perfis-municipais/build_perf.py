# build_perf.py — perfis dos políticos municipais (prefeitos, vices e vereadores) a partir de dados abertos do TSE.
# Roda DEPOIS de mapa/build_mapa.py: acrescenta a chave "_pf" em cada data/mapa/ver-UF.json.
# Fontes: TSE (candidaturas 1996–2026, bens declarados 2024, votação por município/zona 2024), IBGE (Censo 2022).
# CPF e título de eleitor são usados só para cruzar candidaturas da mesma pessoa e nunca são gravados.
import csv, json, re, sys, unicodedata, collections, datetime, os
csv.field_size_limit(10**8)
SC = '/tmp/claude-0/-home-claude/09aefdc5-706f-5d9c-918a-28b3af6171a1/scratchpad'
OUT = f'{SC}/site/data/mapa'
TSE = f'{SC}/gov/tse'
T24 = '/tmp/t24'
sys.path.insert(0, f'{SC}/mapa')

def nrm(s):
    s = unicodedata.normalize('NFD', s or ''); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').upper()
    return re.sub(r'\s+', ' ', re.sub(r"[^A-Z0-9 ]", ' ', s)).strip()
SMALL = {'de','da','do','das','dos','e','d','di','du','del','la'}
def tc(s):
    s = (s or '').strip()
    if not s or s.startswith('#NUL') or s == '-4': return ''
    out = []
    for i, w in enumerate(s.split()):
        lw = w.lower()
        if re.fullmatch(r"[a-z]{1,3}", lw) and not re.search(r'[aeiouáéíóúâêôãõà]', lw) and lw not in SMALL: out.append(w.upper()); continue
        if re.fullmatch(r'(i|ii|iii|iv|v|vi|vii|viii|ix|x)', lw) and i: out.append(w.upper()); continue
        if i and lw in SMALL: out.append(lw); continue
        if "'" in lw:
            a, b = lw.split("'", 1); out.append(a.capitalize() + "'" + b.capitalize()); continue
        out.append('-'.join(p[:1].upper() + p[1:] for p in lw.split('-')))
    return ' '.join(out)
def cap1(s):
    s = (s or '').strip()
    if not s or s.startswith('#N') or s in ('-1', '-3', '-4'): return ''
    s = s.lower(); return s[:1].upper() + s[1:]
def tit(r):
    t = (r.get('NR_TITULO_ELEITORAL_CANDIDATO') or '').strip().lstrip('0')
    return t if t.isdigit() and len(t) >= 8 else None
def nasc(r):
    d = (r.get('DT_NASCIMENTO') or '').strip()
    return d if re.fullmatch(r'\d\d/\d\d/\d{4}', d) else ''

# ---------------- municípios IBGE <-> TSE (mesma regra de build_mapa.py) ----------------
G = json.load(open('/tmp/geo/all.json'))
MUN = {c: (n, uf) for c, n, uf in G['mun']}
ibn = {}
for c, (n, uf) in MUN.items(): ibn.setdefault(uf, {})[nrm(n)] = c
MANUAL = {'05290': 1506500, '44571': 3122900, '17035': 2405306, '04120': 1502954, '00256': 1100098, '41092': 3105509, '31011': 2800100,
          '53031': 3165206, '03158': 1400605, '34118': 2905602, '91553': 5107800, '71013': 3550001, '00337': 1100346}
print('lendo candidaturas 2024…', file=sys.stderr)
R24 = list(csv.DictReader(open(f'{TSE}/consulta_cand_2024_BRASIL.csv', encoding='latin1'), delimiter=';'))
tse2ibge = {}
for r in R24:
    ue = r['SG_UE']
    if ue not in tse2ibge: tse2ibge[ue] = MANUAL.get(ue) or ibn.get(r['SG_UF'], {}).get(nrm(r['NM_UE']))
by = collections.defaultdict(list)
for r in R24: by[tse2ibge[r['SG_UE']]].append(r)
def dt(s): d, m, y = s.split('/'); return datetime.date(int(y), int(m), int(d))

# ---------------- votação 2024 (soma das zonas) ----------------
print('lendo votação 2024…', file=sys.stderr)
VOT = collections.Counter()           # (sq, turno) -> votos nominais válidos
TOT = collections.Counter()           # (eleição, ue, cargo, turno) -> soma
GRP = collections.defaultdict(set)    # (eleição, ue, cargo, turno) -> sqs
SQG = {}
for r in csv.DictReader(open(f'{T24}/votacao_candidato_munzona_2024_BRASIL.csv', encoding='latin1'), delimiter=';'):
    v = int(r['QT_VOTOS_NOMINAIS_VALIDOS'] or 0)
    k = (r['CD_ELEICAO'], r['SG_UE'], r['DS_CARGO'].upper(), r['NR_TURNO'])
    VOT[(r['SQ_CANDIDATO'], r['NR_TURNO'])] += v; TOT[k] += v; GRP[k].add(r['SQ_CANDIDATO']); SQG[(r['SQ_CANDIDATO'], r['NR_TURNO'])] = k
RANK = {}
for k, sqs in GRP.items():
    L = sorted(sqs, key=lambda s: -VOT[(s, k[3])])
    for i, s in enumerate(L): RANK[(s, k[3])] = (i + 1, len(L))

# ---------------- bens declarados 2024 ----------------
print('lendo bens 2024…', file=sys.stderr)
def bcat(c):
    c = int(c)
    if 1 <= c <= 19: return 0      # imóveis
    if c in (21, 22, 23): return 1 # veículos, barcos e aeronaves
    if 41 <= c <= 79 or c in (95, 97): return 2  # dinheiro, contas e aplicações
    if c in (31, 32, 39): return 3 # participação em empresas
    return 4
BENS = collections.defaultdict(lambda: [0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0])
for r in csv.DictReader(open(f'{T24}/bem_candidato_2024_BRASIL.csv', encoding='latin1'), delimiter=';'):
    v = float((r['VR_BEM_CANDIDATO'] or '0').replace('.', '').replace(',', '.') or 0)
    b = BENS[r['SQ_CANDIDATO']]; b[0] += v; b[1] += 1; b[2 + bcat(r['CD_TIPO_BEM_CANDIDATO'])] += v

# ---------------- pessoas exibidas no mapa ----------------
VERF = {f[4:6]: json.load(open(f'{OUT}/{f}')) for f in os.listdir(OUT) if f.startswith('ver-')}
STF = {f[3:5]: json.load(open(f'{OUT}/{f}')) for f in os.listdir(OUT) if f.startswith('st-')}
CARGO = {'P': 'PREFEITO', 'VP': 'VICE-PREFEITO', 'V': 'VEREADOR'}
ELEITO = {'ELEITO', 'ELEITO POR QP', 'ELEITO POR MÉDIA'}
def find(code, k, p):
    L = [r for r in by.get(code, []) if r['DS_CARGO'] == CARGO[k] and r['NR_CANDIDATO'] == p[3]]
    if len(L) > 1:
        M = [r for r in L if tc(r['NM_URNA_CANDIDATO']) == p[0]] or L
        E = [r for r in M if r['DS_SIT_TOT_TURNO'] in ELEITO] or M
        L = sorted(E, key=lambda r: (dt(r['DT_ELEICAO']), r['NR_TURNO']))
    return L[-1] if L else None
PEOPLE = []   # (uf, code, k, pessoa, linha TSE)
miss = collections.Counter()
for uf, S in STF.items():
    mun = S['d']['mun'] if 'd' in S else S['mun']
    for code, m in mun.items():
        code = int(code)
        for fld, k in (('p', 'P'), ('v', 'VP'), ('af', 'P'), ('afv', 'VP')):
            p = m.get(fld)
            if p and not p[5]:
                r = find(code, k, p)
                if r: PEOPLE.append((uf, code, k, p, r))
                else: miss[k] += 1
        V = VERF.get(uf, {}).get(str(code))
        for p in (V[0] if V else []):
            if p[5]: continue
            r = find(code, 'V', p)
            if r: PEOPLE.append((uf, code, 'V', p, r))
            else: miss['V'] += 1
print(len(PEOPLE), 'pessoas; sem par no TSE:', dict(miss), file=sys.stderr)

# ---------------- histórico de candidaturas (1996–2026) ----------------
bytit = collections.defaultdict(list); bynb = collections.defaultdict(list)
for i, (_, _, _, _, r) in enumerate(PEOPLE):
    t = tit(r)
    if t: bytit[t].append(i)
    if nasc(r): bynb[(nrm(r['NM_CANDIDATO']), nasc(r))].append(i)
HIST = collections.defaultdict(dict)
for y in range(1996, 2027, 2):
    print('histórico', y, file=sys.stderr)
    for r in csv.DictReader(open(f'{TSE}/consulta_cand_{y}_BRASIL.csv', encoding='latin1'), delimiter=';'):
        t = tit(r)
        ids = bytit.get(t) if t else None
        if not ids and nasc(r): ids = bynb.get((nrm(r.get('NM_CANDIDATO', '')), nasc(r)))
        if not ids: continue
        for i in ids:
            key = (y, r['SQ_CANDIDATO'])
            e = HIST[i].get(key)
            if not e:
                e = HIST[i][key] = {'y': y, 'c': r['DS_CARGO'], 'l': r['NM_UE'], 'uf': r['SG_UF'], 'p': r['SG_PARTIDO'], 'n': r['NR_CANDIDATO'],
                                    'd': r.get('DT_ELEICAO', ''), 'sit': [], 'sq': r['SQ_CANDIDATO'], 'ue': r['SG_UE']}
            e['sit'].append((r.get('NR_TURNO', '1'), r.get('DS_SIT_TOT_TURNO', '')))
def res(sits):
    s = sorted(set(sits)); fin = s[-1][1] if s else ''
    if fin.startswith('#') or fin in ('', '-1'): return ''
    if fin in ELEITO or fin in ('MÉDIA', 'MEDIA', 'ELEITO POR QP'): return 'Eleito'
    return cap1(fin)
CG = {'PREFEITO': 'Prefeito', 'VICE-PREFEITO': 'Vice-prefeito', 'VEREADOR': 'Vereador', 'DEPUTADO ESTADUAL': 'Deputado estadual', 'DEPUTADO FEDERAL': 'Deputado federal',
      'DEPUTADO DISTRITAL': 'Deputado distrital', 'SENADOR': 'Senador', 'GOVERNADOR': 'Governador', 'VICE-GOVERNADOR': 'Vice-governador', 'PRESIDENTE': 'Presidente',
      'VICE-PRESIDENTE': 'Vice-presidente', '1º SUPLENTE': '1º suplente de senador', '2º SUPLENTE': '2º suplente de senador', '1º SUPLENTE SENADOR': '1º suplente de senador',
      '2º SUPLENTE SENADOR': '2º suplente de senador'}
def cargo(c): return CG.get(c.upper().strip(), cap1(c))
UFNOME = {s: n for c, s, n, reg in G['estados']}
import bens_all
_need = {(y, e['ue'], sqh) for i in HIST for (y, sqh), e in HIST[i].items() if y >= 2006}
BY = bens_all.load(_need)
import sal_pb
SALPB = sal_pb.load()

# ---------------- montagem ----------------
POP = json.load(open(f'{SC}/mun/pop2022.json'))
TAB = {'o': [], 'i': [], 'e': [], 'r': [], 'c': [], 's': []}; IDX = {k: {} for k in TAB}
def code_of(t, s):
    s = s or ''
    if s not in IDX[t]: IDX[t][s] = len(TAB[t]); TAB[t].append(s)
    return IDX[t][s]
PF = collections.defaultdict(lambda: collections.defaultdict(dict))
stats = collections.Counter()
for i, (uf, code, k, p, r) in enumerate(PEOPLE):
    sq = r['SQ_CANDIDATO']
    rec = {'u': p[0]}
    if nasc(r): rec['b'] = nasc(r)
    if r.get('SG_UF_NASCIMENTO') and len(r['SG_UF_NASCIMENTO']) == 2 and r['SG_UF_NASCIMENTO'] in UFNOME: rec['bu'] = r['SG_UF_NASCIMENTO']
    rec['o'] = code_of('o', cap1(r['DS_OCUPACAO'])); rec['i'] = code_of('i', cap1(r['DS_GRAU_INSTRUCAO']))
    rec['e'] = code_of('e', cap1(r['DS_ESTADO_CIVIL'])); rec['r'] = code_of('r', cap1(r['DS_COR_RACA']))
    rec['el'] = r['DT_ELEICAO']
    if r['NM_TIPO_ELEICAO'] != 'ELEIÇÃO ORDINÁRIA': rec['sp'] = 1
    # votos (vice: votos da chapa)
    vsq = sq
    if k == 'VP':
        tit_r = [x for x in by.get(code, []) if x['DS_CARGO'] == 'PREFEITO' and x['NR_CANDIDATO'] == r['NR_CANDIDATO'] and x['CD_ELEICAO'] == r['CD_ELEICAO']]
        vsq = tit_r[-1]['SQ_CANDIDATO'] if tit_r else None
        if tit_r: rec['ch'] = tc(tit_r[-1]['NM_URNA_CANDIDATO'])
    if vsq:
        turnos = [t for t in ('2', '1') if (vsq, t) in VOT]
        if turnos:
            t = turnos[0]; g = SQG[(vsq, t)]; v = VOT[(vsq, t)]
            rk, n = RANK[(vsq, t)]
            rec['vt'] = [v, round(100 * v / TOT[g], 2) if TOT[g] else None, rk, n, int(t)]
            stats['com_votos'] += 1
    b = BENS.get(sq)
    rec['bn'] = [round(x) for x in b[:1]] + [b[1]] + [round(x) for x in b[2:]] if b else [0, 0]
    # histórico
    H = []
    mn, muf = MUN[code]
    for (y, sqh), e in sorted(HIST.get(i, {}).items()):
        loc = tc(e['l']); cg = cargo(e['c'])
        lc = 0 if (nrm(loc) == nrm(mn) and e['uf'] == muf) else (1 if e['uf'] == muf and nrm(loc) == nrm(UFNOME.get(muf, '')) else loc)
        H.append([y, code_of('c', cg), lc, e['uf'] if e['uf'] != muf else 0, e['p'], e['n'], code_of('s', res(e['sit'])), 1 if any(t == '2' for t, _ in e['sit']) else 0, BY.get((y, e['ue'], sqh)) if y >= 2006 else None])
    seen = set(); HH = []
    for h in H:
        kk = (h[0], h[1], h[2], h[6])
        if kk in seen: continue
        seen.add(kk); HH.append(h)
    rec['h'] = HH; stats['hist'] += len(HH)
    if uf == 'PB':
        sl = SALPB.get((nrm(MUN[code][0]), nrm(r['NM_CANDIDATO'])))
        if sl: rec['sl'] = sl[:2]; stats['sal_pb'] += 1
        else: stats['sal_pb_falta'] += 1
    PF[uf][str(code)].setdefault(k + p[3], []).append(rec)
    stats[k] += 1
print(dict(stats), file=sys.stderr)
# arquivos: perfis agrupados por estados (o site tem limite de arquivos), carregados só ao abrir um perfil
NG = 8
# grupos fixos (o site referencia esta tabela em PFG)
FIX = {"MG":0,"SP":1,"RS":2,"SE":2,"TO":2,"AC":3,"BA":3,"RN":3,"RO":3,"AL":4,"CE":4,"PR":4,"MS":5,"PE":5,"RJ":5,"SC":5,"ES":6,"GO":6,"MT":6,"PI":6,"RR":6,"AM":7,"AP":7,"MA":7,"PA":7,"PB":7}
bins = [[0, [u for u in FIX if FIX[u] == i]] for i in range(NG)]
GMAP = {}
for i, (_, ufs) in enumerate(bins):
    o = {'t': TAB, 'pop': {}, 'uf': {}}
    for uf in sorted(ufs):
        GMAP[uf] = i; o['uf'][uf] = PF[uf]
        for c in PF[uf]: o['pop'][c] = POP.get(c)
    json.dump(o, open(f'{OUT}/pf-{i}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('pf-%d' % i, sorted(ufs), os.path.getsize(f'{OUT}/pf-{i}.json'), file=sys.stderr)
print('GMAP', json.dumps(GMAP, separators=(',', ':')))
