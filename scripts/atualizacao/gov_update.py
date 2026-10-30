# gov_update.py — atualiza a aba Governo (perfis) do Aquarela Brasil só com o que mudou.
# Pasta de trabalho W:
#   W/site/  perfis.json vcam.json vsen.json gov_idx.json gov_meta.json  e  W/site/p/<arquivos de perfil necessários>.json
#   W/col/   cam.json (coletor da Câmara) e sen.json (coletor do Senado)
# Comandos:
#   python3 -I gov_update.py ids   W   -> imprime os ids de deputados (DEP) e senadores (SENS) para os coletores e a data inicial
#   python3 -I gov_update.py need  W   -> W/col/need.json (arquivos data/p/... que precisam ser baixados do site)
#   python3 -I gov_update.py merge W   -> grava os arquivos alterados em W/site; lista em W/col/changed.json; imprime resumo
import json, sys, os, re, unicodedata, datetime
cmd, W = sys.argv[1], sys.argv[2]
S, C = os.path.join(W, 'site'), os.path.join(W, 'col')
ld = lambda p, d=None: json.load(open(p, encoding='utf-8')) if os.path.exists(p) else d
def dump(p, o): json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
PF = ld(f'{S}/perfis.json'); PERF = PF['perf']
IDX = ld(f'{S}/gov_idx.json', {'f': [], 'p': {}, 's': {}})
META = ld(f'{S}/gov_meta.json', {})
def slug(s):
    s = unicodedata.normalize('NFD', s); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')
def fname(k):
    kind, uf, n = k.split('|'); return f'{kind}-{uf.lower()}-{slug(n)}'
DEP, SEN = {}, {}
for k, v in PERF.items():
    if v.get('cam'): DEP.setdefault(int(v['cam']['id']), []).append(k)
    if v.get('sen'): SEN.setdefault(int(v['sen']['cod']), []).append(k)
if cmd == 'ids':
    print('DEP=' + json.dumps(sorted(DEP), separators=(',', ':')))
    print('SENS=' + json.dumps(sorted(SEN), separators=(',', ':')))
    print('desde=' + str(min(META.get('cam', '2026-10-14'), META.get('sen', '2026-10-15'))))
    sys.exit()
MAIN = {'PL','PLP','PEC','PDL','PDC','PRC','PLV','PFC','PDS'}
SMAIN = ('Projeto de Lei Ordinária','Projeto de Lei Complementar','Proposta de Emenda à Constituição','Projeto de Decreto Legislativo','Projeto de Resolução','Proposta de Fiscalização e Controle')
LAWC = 'Transformado em Norma Jurídica'
cam = ld(f'{C}/cam.json', {'janela': [None, None], 'exercicio': [], 'votacoes': [], 'L': [], 'st': [], 'novas': []})
sen = ld(f'{C}/sen.json', {'votacoes': [], 'processos': {}})
CL = cam['L']
SIT = PF['sit']
def sitname(i): return SIT[i] if isinstance(i, int) and i < len(SIT) else ''
# ---------- quem muda ----------
touch = set()
for v in cam['votacoes']:
    for dep, tipo, part in v['votos']:
        for k in DEP.get(int(dep), []): touch.add(fname(k))
for pid, li in cam['st']:
    p = str(pid)
    if p in IDX['p'] and sitname(IDX['s'].get(p, 0)) != CL[li]:
        for i in IDX['p'][p]: touch.add(IDX['f'][i])
for n in cam['novas']:
    for dep, ordem in n[8]:
        for k in DEP.get(int(dep), []): touch.add(fname(k))
for v in sen['votacoes']:
    for cod, sig in v['votos']:
        for k in SEN.get(int(cod), []): touch.add(fname(k))
for cod, rows in sen['processos'].items():
    if rows:
        for k in SEN.get(int(cod), []): touch.add(fname(k))
if cmd == 'need':
    dump(f'{C}/need.json', ['data/p/' + f + '.json' for f in sorted(touch)])
    print(len(touch), 'arquivos de perfil a baixar'); sys.exit()
# ---------- merge ----------
VC = ld(f'{S}/vcam.json'); VS = ld(f'{S}/vsen.json')
SITI = {s: i for i, s in enumerate(SIT)}
def sidx(s):
    s = s or ''
    if s not in SITI: SITI[s] = len(SIT); SIT.append(s)
    return SITI[s]
P = {}
def pfile(f):
    if f not in P: P[f] = ld(f'{S}/p/{f}.json', {})
    return P[f]
f2k = {fname(k): k for k in PERF}
changed = set(); pessoas = set()
rep = {'votacoes_camara': 0, 'votacoes_senado': 0, 'votos_novos': 0, 'props_novas': [], 'situacoes': []}
exer = {int(x) for x in cam['exercicio']}
def cvotos(k):
    c = PERF[k]['cam']; v = c.get('votos')
    if not v: v = c['votos'] = {'n': 0, 'plen': 0, 'den': 0, 'part': None, 'de': None, 'ate': None, 'pm': 0}
    if 'pm' not in v: v['pm'] = round((v.get('part') or 0) * v.get('den', 0) / 100)
    return v
VCN = {'Sim': 'S', 'Não': 'N', 'Obstrução': 'O', 'Artigo 17': 'P', 'Abstenção': 'A', 'Branco': 'B'}
for v in sorted(cam['votacoes'], key=lambda x: (x['data'], x['id'])):
    vid = v['id']; novo = vid not in VC
    if novo: VC[vid] = [v['data'], v['org'], v['desc'], v['aprov'], v['sim'], v['nao'], v['out'], v['props']]; rep['votacoes_camara'] += 1
    votou = {int(dep): VCN.get(tipo, '?') for dep, tipo, _ in v['votos']}
    for dep, code in votou.items():
        for k in DEP.get(dep, []):
            f = fname(k); d = pfile(f); cv = d.setdefault('cv', [])
            if any(x.split(',')[0] == vid for x in cv): continue
            cv.append(f'{vid},{code}'); changed.add(f); pessoas.add(k); rep['votos_novos'] += 1
            s = cvotos(k); s['n'] += 1; y = v['data'][:4]
            if v['org'] == 'PLEN': s['plen'] += 1
            s['de'] = min(s['de'] or y, y); s['ate'] = max(s['ate'] or y, y)
    if novo and v['org'] == 'PLEN':
        for dep in exer:
            for k in DEP.get(dep, []):
                s = cvotos(k); s['den'] += 1
                if dep in votou: s['pm'] += 1
                s['part'] = round(100 * s['pm'] / s['den'], 1)
def camstats(k, d):
    rows = d.get('cp', []); c = PERF[k].setdefault('cam', {})
    c['props'] = {'tot': len(rows), 'leg': sum(1 for r in rows if r[1] in MAIN), 'lm': sum(1 for r in rows if r[1] in MAIN and r[7]),
                  'lei': sum(1 for r in rows if r[1] in MAIN and SIT[r[5]] == LAWC)}
# situação de proposições já conhecidas
for pid, li in cam['st']:
    p = str(pid); sit = CL[li]
    if p not in IDX['p'] or sitname(IDX['s'].get(p, 0)) == sit: continue
    IDX['s'][p] = sidx(sit)
    for i in IDX['p'][p]:
        f = IDX['f'][i]; d = pfile(f)
        for r in d.get('cp', []):
            if r[0] == pid and SIT[r[5]] != sit:
                old = SIT[r[5]]; r[5] = sidx(sit); changed.add(f); pessoas.add(f2k.get(f, f))
                if sit == LAWC or old == LAWC: rep['situacoes'].append(f'{r[1]} {r[2]}/{r[3]}: {sit}')
# proposições novas de deputados com perfil
for pid, sig, num, ano, dt, em, li, tdesc, aut in cam['novas']:
    st = CL[li]
    if sig not in PF['tipos'] and tdesc: PF['tipos'][sig] = tdesc
    if sig not in PF['grp']: PF['grp'][sig] = 'leg' if sig in MAIN else 'req' if sig.startswith(('REQ', 'RIC', 'INC')) else 'emd' if sig.startswith('EM') else 'par' if sig.startswith(('PRL', 'PAR', 'PPR')) else 'out'
    for dep, ordem in aut:
        for k in DEP.get(int(dep), []):
            f = fname(k); d = pfile(f); cp = d.setdefault('cp', [])
            if any(r[0] == pid for r in cp): continue
            cp.append([pid, sig, num, ano, (dt or '').replace('-', ''), sidx(st), em if sig in MAIN else em[:180], 1 if int(ordem or 0) == 1 else 0])
            changed.add(f); pessoas.add(k)
            if sig in MAIN: rep['props_novas'].append(f'{sig} {num}/{ano} ({k.split("|")[2]})')
            if f not in IDX['f']: IDX['f'].append(f)
            fi = IDX['f'].index(f); li2 = IDX['p'].setdefault(str(pid), [])
            if fi not in li2: li2.append(fi)
            IDX['s'][str(pid)] = sidx(st)
for f in changed:
    k = f2k.get(f)
    if k and 'cp' in P[f]: camstats(k, P[f])
# ---------- Senado ----------
PRES = {'Sim', 'Não', 'Abstenção', 'Votou', 'P-NRV', 'Presidente (art. 51 RISF)', 'P-OD'}
sig_old = {(v[0], v[6], v[1]) for v in VS.values()}
for v in sorted(sen['votacoes'], key=lambda x: (x['data'], x['k'])):
    key = v['k']
    if key in VS or (v['data'], v['ident'], v['desc']) in sig_old: continue
    VS[key] = [v['data'], v['desc'], v['res'], str(v['sim']), str(v['nao']), str(v['abs']), v['ident'], (v['ementa'] or '')[:400], v['sec']]; rep['votacoes_senado'] += 1
    for cod, sg in v['votos']:
        for k in SEN.get(int(cod), []):
            f = fname(k); d = pfile(f); sv = d.setdefault('sv', [])
            sv.append(f'{key},{sg}'); changed.add(f); pessoas.add(k); rep['votos_novos'] += 1
            s = PERF[k]['sen'].setdefault('votos', {'n': 0, 'pres': 0, 'part': None, 'de': None, 'ate': None})
            s['n'] += 1; s['pres'] += 1 if sg in PRES else 0; s['part'] = round(100 * s['pres'] / s['n'], 1)
            y = v['data'][:4]; s['de'] = min(s['de'] or y, y); s['ate'] = max(s['ate'] or y, y)
for cod, lista in sen['processos'].items():
    for k in SEN.get(int(cod), []):
        f = fname(k); d = pfile(f); rows = d.setdefault('sp', []); pos = {r[0]: i for i, r in enumerate(rows)}; mudou = False
        for cm, ident, tipo, dt, sit, em, aut, norma in lista:
            isM = tipo in SMAIN
            new = [cm, ident, tipo, (dt or '').replace('-', '')[:8], sidx(sit), (em or '').strip() if isM else (em or '').strip()[:180], 0 if aut == 'e outros' else 1, norma or '']
            if cm in pos:
                o = rows[pos[cm]]; new[6] = o[6]
                if o != new:
                    if norma and not o[7] and isM: rep['situacoes'].append(f'{ident}: {norma}')
                    rows[pos[cm]] = new; mudou = True
            else:
                rows.append(new); pos[cm] = len(rows) - 1; mudou = True
                if isM: rep['props_novas'].append(f'{ident} ({k.split("|")[2]})')
        if mudou:
            rows.sort(key=lambda r: r[3]); changed.add(f); pessoas.add(k)
            PERF[k]['sen']['props'] = {'tot': len(rows), 'leg': sum(1 for r in rows if r[2] in SMAIN), 'lm': sum(1 for r in rows if r[2] in SMAIN and r[6]), 'lei': sum(1 for r in rows if r[2] in SMAIN and r[7])}
# ---------- grava ----------
os.makedirs(f'{S}/p', exist_ok=True)
out = []
for f in sorted(changed):
    dump(f'{S}/p/{f}.json', P[f]); out.append(f'data/p/{f}.json')
hoje = cam['janela'][1] or datetime.date.today().isoformat()
META.update({'cam': hoje, 'sen': hoje, 'atualizado': datetime.date.fromisoformat(hoje).strftime('%d/%m/%Y')})
dump(f'{S}/perfis.json', PF); dump(f'{S}/vcam.json', VC); dump(f'{S}/vsen.json', VS); dump(f'{S}/gov_idx.json', IDX); dump(f'{S}/gov_meta.json', META)
out += ['data/perfis.json', 'data/vcam.json', 'data/vsen.json', 'data/gov_idx.json', 'data/gov_meta.json']
dump(f'{C}/changed.json', out)
rep['pessoas'] = len(pessoas); rep['arquivos'] = len(out)
u = list(dict.fromkeys(x.split(' (')[0] for x in rep['props_novas'])); rep['props_novas'] = {'total': len(u), 'exemplos': u[:15]}
rep['situacoes'] = list(dict.fromkeys(rep['situacoes']))[:30]
print(json.dumps(rep, ensure_ascii=False, indent=1))
