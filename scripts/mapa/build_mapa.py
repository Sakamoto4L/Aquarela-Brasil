# build_mapa.py — gera os dados da aba Mapa (quem governa cada estado e cada município)
# Fontes: IBGE (malhas e lista de municípios), TSE (candidaturas 2022, 2024 e 2026), Câmara e Senado (em exercício hoje).
# O CPF é usado só internamente para cruzar candidaturas e nunca é gravado nos arquivos de saída.
import csv, json, re, os, sys, unicodedata, collections, datetime
SC = '/tmp/claude-0/-home-claude/09aefdc5-706f-5d9c-918a-28b3af6171a1/scratchpad'
OUT = f'{SC}/site/data/mapa'; os.makedirs(OUT, exist_ok=True)
for _f in os.listdir(OUT): os.remove(f'{OUT}/{_f}')
G = json.load(open('/tmp/geo/all.json'))
HOJE = datetime.date(2026, 10, 29)
def dump(name, o):
    json.dump(o, open(f'{OUT}/{name}', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
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
def gen(r): return 'F' if r.get('DS_GENERO', '').startswith('FEM') else 'M'
ELEITO = {'ELEITO', 'ELEITO POR QP', 'ELEITO POR MÉDIA'}
def read(path):
    return list(csv.DictReader(open(path, encoding='latin1'), delimiter=';'))
def dt(s): d, m, y = s.split('/'); return datetime.date(int(y), int(m), int(d))
# ---------------- perfis do site (para ligar pessoas às páginas de perfil) ----------------
PF = json.load(open(f'{SC}/site/data/perfis.json'))['perf']
IDENT = json.load(open(f'{SC}/gov/ident.json'))
tit2key = {}
for k, v in IDENT.items():
    if v.get('titulo'): tit2key.setdefault(v['titulo'], k)
def TIT(r):
    t = r.get('NR_TITULO_ELEITORAL_CANDIDATO', '')
    return t if t.isdigit() and len(t) >= 10 else None
cam2key = {int(v['cam']['id']): k for k, v in PF.items() if v.get('cam')}
sen2key = {int(v['sen']['cod']): k for k, v in PF.items() if v.get('sen')}
def P(r, extra=''):
    """pessoa compacta: [nome de urna, nome completo, partido, número, gênero, chave do perfil, observação]"""
    soc = tc(r.get('NM_SOCIAL_CANDIDATO', ''))
    return [tc(r['NM_URNA_CANDIDATO']), soc or tc(r['NM_CANDIDATO']), r['SG_PARTIDO'], r['NR_CANDIDATO'], gen(r), tit2key.get(TIT(r) or '-', ''), extra]
# ---------------- municípios: IBGE <-> TSE ----------------
MUN = {c: (n, uf) for c, n, uf in G['mun']}
ibn = {}
for c, (n, uf) in MUN.items(): ibn.setdefault(uf, {})[nrm(n)] = c
MANUAL = {'05290': 1506500, '44571': 3122900, '17035': 2405306, '04120': 1502954, '00256': 1100098, '41092': 3105509, '31011': 2800100,
          '53031': 3165206, '03158': 1400605, '34118': 2905602, '91553': 5107800, '71013': 3550001, '00337': 1100346}
R24 = read('/tmp/tse/z2024/consulta_cand_2024_BRASIL.csv')
R26 = read('/tmp/tse/z2026/consulta_cand_2026_BRASIL.csv')
R22 = read('/tmp/tse/z2022/consulta_cand_2022_BRASIL.csv')
tse2ibge = {}
for r in R24:
    ue = r['SG_UE']
    if ue in tse2ibge: continue
    tse2ibge[ue] = MANUAL.get(ue) or ibn.get(r['SG_UF'], {}).get(nrm(r['NM_UE']))
assert all(tse2ibge.values()), [k for k, v in tse2ibge.items() if not v]
# candidaturas de 2026 por CPF (quem disputou 2026 precisou deixar cargo executivo até abril)
cand26 = {}
for r in R26:
    if TIT(r): cand26.setdefault(TIT(r), []).append(r)
def cargo26(t):
    L = cand26.get(t) or [] if t else []
    return L[0]['DS_CARGO'].capitalize() if L else ''
# ---------------- eleições municipais (2024 + suplementares) ----------------
by = collections.defaultdict(list)
for r in R24: by[tse2ibge[r['SG_UE']]].append(r)
CAPS = {}  # capital de cada UF
capnames = {'AC':'Rio Branco','AL':'Maceió','AP':'Macapá','AM':'Manaus','BA':'Salvador','CE':'Fortaleza','ES':'Vitória','GO':'Goiânia','MA':'São Luís','MT':'Cuiabá','MS':'Campo Grande','MG':'Belo Horizonte','PA':'Belém','PB':'João Pessoa','PR':'Curitiba','PE':'Recife','PI':'Teresina','RJ':'Rio de Janeiro','RN':'Natal','RS':'Porto Alegre','RO':'Porto Velho','RR':'Boa Vista','SC':'Florianópolis','SP':'São Paulo','SE':'Aracaju','TO':'Palmas','DF':'Brasília'}
for c, (n, uf) in MUN.items():
    if capnames.get(uf) == n: CAPS[uf] = c
munout = collections.defaultdict(dict); stats = collections.Counter()
for code, rows in by.items():
    n, uf = MUN[code]
    elec = collections.defaultdict(list)
    for r in rows: elec[(dt(r['DT_ELEICAO']), r['NM_TIPO_ELEICAO'], r['DS_ELEICAO'])].append(r)
    ordem = sorted(elec)  # por data
    rec = {}
    pref = vice = None; fonte = None; t2 = False; pend = None
    for key in ordem:
        d, tipo, desc = key; rr = elec[key]
        pe = [r for r in rr if r['DS_CARGO'] == 'PREFEITO' and r['DS_SIT_TOT_TURNO'] == 'ELEITO']
        if pe:
            p = pe[-1]; pref = p
            vv = [r for r in rr if r['DS_CARGO'] == 'VICE-PREFEITO' and r['DS_SIT_TOT_TURNO'] == 'ELEITO' and r['NR_CANDIDATO'] == p['NR_CANDIDATO']]
            vice = vv[-1] if vv else None
            fonte = (d, tipo); t2 = p['NR_TURNO'] == '2'; pend = None
        elif tipo != 'ELEIÇÃO ORDINÁRIA' and any(r['DS_CARGO'] in ('PREFEITO', 'VICE-PREFEITO') for r in rr):
            pend = d  # suplementar sem eleito (futura ou sem resultado)
    if pref:
        rec['p'] = P(pref); rec['v'] = P(vice) if vice else None
        rec['el'] = fonte[0].strftime('%d/%m/%Y'); rec['sup'] = 1 if fonte[1] != 'ELEIÇÃO ORDINÁRIA' else 0; rec['t2'] = 1 if t2 else 0
        stats['prefeitos'] += 1
        # deixou o cargo para disputar 2026?
        cp = cargo26(TIT(pref)); cv = cargo26(TIT(vice)) if vice else ''
        if fonte[0] >= datetime.date(2026, 4, 5): cp = ''  # eleito depois do prazo de renúncia: não se aplica
        if cp and not pend:
            if cv:
                rec['ex'] = ['camara', f'{rec["p"][0]} renunciou para disputar a eleição de 2026 ({cp.lower()}), e {rec["v"][0]} também ({cv.lower()}). Pela lei, a prefeitura passa ao presidente da Câmara Municipal.']
                stats['interinos'] += 1
            else:
                rec['ex'] = ['vice', f'{rec["p"][0]} renunciou em abril de 2026 para disputar a eleição de 2026 ({cp.lower()}). Desde então, {rec["v"][0] if rec["v"] else "o vice"} é o prefeito em exercício.']
                stats['vices_em_exercicio'] += 1
    if pend:
        fut = pend > HOJE
        rec['ex'] = ['supl', f'O mandato de quem venceu em {rec.get("el","2024")} foi cassado. ' + (f'A eleição suplementar está marcada para {pend.strftime("%d/%m/%Y")}; até lá, a prefeitura é exercida interinamente.' if fut else f'A eleição suplementar de {pend.strftime("%d/%m/%Y")} não tem eleito registrado no TSE; a prefeitura é exercida interinamente.')]
        stats['suplementar_pendente'] += 1
    # vereadores
    vo = [r for r in elec[ordem[0]] if r['DS_CARGO'] == 'VEREADOR' and r['DS_SIT_TOT_TURNO'] in ELEITO and r['NM_TIPO_ELEICAO'] == 'ELEIÇÃO ORDINÁRIA']
    ver = sorted((P(r) for r in vo), key=lambda p: (p[2], nrm(p[0])))
    for key in ordem[1:]:
        vs = [r for r in elec[key] if r['DS_CARGO'] == 'VEREADOR' and r['DS_SIT_TOT_TURNO'] in ELEITO]
        if not vs: continue
        if len(vs) >= max(1, len(ver)) // 2:
            ver = sorted((P(r) for r in vs), key=lambda p: (p[2], nrm(p[0]))); rec['vsup'] = f'Câmara Municipal renovada em eleição suplementar em {key[0].strftime("%d/%m/%Y")}.'
        else:
            rec['vsup'] = f'Eleição suplementar para vereador em {key[0].strftime("%d/%m/%Y")}: ' + ', '.join(f'{tc(r["NM_URNA_CANDIDATO"])} ({r["SG_PARTIDO"]})' for r in vs) + '.'
    rec['ver'] = ver; stats['vereadores'] += len(ver)
    munout[uf][code] = rec
# ---------------- correções verificadas (29/10/2026) ----------------
# O arquivo de candidaturas do TSE não registra algumas decisões judiciais recentes. Estas correções vêm do
# sistema de resultados do TSE (resultados.tse.jus.br), do calendário de eleições suplementares do TSE e de notícias.
def mrow(code, cargo, nr, tipo='ELEIÇÃO ORDINÁRIA'):
    L = [r for r in by[code] if r['DS_CARGO'] == cargo and r['NR_CANDIDATO'] == nr and r['NM_TIPO_ELEICAO'] == tipo]
    return L[-1] if L else None
def ela(r): return 'a' if r and gen(r) == 'F' else 'o'
# (A) totalização do TSE ainda não definitiva: ninguém marcado como eleito; mostramos a candidatura válida mais votada
PEND = {5210208: '70', 5200852: '45', 2100709: '15', 2104909: '43', 2110237: '22', 2800605: '55', 2801603: '44', 2804805: '23'}
for code, nr in PEND.items():
    n, uf = MUN[code]; rec = munout[uf][code]; pr = mrow(code, 'PREFEITO', nr); vr = mrow(code, 'VICE-PREFEITO', nr)
    rec.update({'p': P(pr), 'v': P(vr) if vr else None, 'el': '06/10/2024', 'sup': 0, 't2': 0,
                'ex': ['pend', f'{rec.get("p", P(pr))[0]} foi {ela(pr)} mais votad{ela(pr)} em 2024 entre as candidaturas válidas. No sistema de resultados do TSE, a totalização deste município ainda não é definitiva (há candidatura com votos anulados sob recurso), por isso ninguém aparece formalmente como eleito.']})
    stats['prefeitos'] += 1
# Iporá (GO): o arquivo de candidaturas também não marca os vereadores; vagas por partido do sistema de resultados do TSE
ipv = json.load(open('/tmp/mapa/res/ipora_ver.json')); nums = {c[2] for a in ipv for c in a[2]}
vr = [r for r in by[5210208] if r['DS_CARGO'] == 'VEREADOR' and r['NR_CANDIDATO'] in nums and r['NM_TIPO_ELEICAO'] == 'ELEIÇÃO ORDINÁRIA']
munout['GO'][5210208]['ver'] = sorted((P(r) for r in vr), key=lambda p: (p[2], nrm(p[0])))
munout['GO'][5210208]['vsup'] = 'Distribuição de vagas ainda provisória no sistema de resultados do TSE (totalização não definitiva).'
stats['vereadores'] += len(vr)
# (B) o mais votado teve os votos anulados e não há eleito; até decisão final ou nova eleição, o presidente da Câmara assume
ANUL = {3141603: ('33', 'O mais votado em 2024, {n} ({pt}), teve os votos anulados pela Justiça Eleitoral, em decisão ainda sob recurso, e o TSE não registra prefeito eleito. Pela lei, até a decisão final ou uma nova eleição, a prefeitura é exercida pelo presidente da Câmara Municipal.'),
        2403400: ('15', 'O mais votado em 2024, {n} ({pt}), teve os votos anulados pela Justiça Eleitoral, em decisão ainda sob recurso (totalização refeita pelo TSE em 27/10/2026), e não há prefeito eleito. Pela lei, até a decisão final ou uma nova eleição, a prefeitura é exercida pelo presidente da Câmara Municipal.'),
        3551207: ('10', 'O mais votado em 2024, {n} ({pt}), teve os votos anulados pela Justiça Eleitoral. Uma nova eleição está marcada para 06/12/2026 (calendário do TSE); até a posse, a prefeitura é exercida pelo presidente da Câmara Municipal.')}
for code, (nr, txt) in ANUL.items():
    n, uf = MUN[code]; rec = munout[uf][code]; r = mrow(code, 'PREFEITO', nr)
    rec['af'] = P(r); rec['ex'] = ['supl', txt.format(n=rec['af'][0], pt=r['SG_PARTIDO'])]
    stats['suplementar_pendente'] += 1
munout['SP'][3532207]['ex'] = ['supl', 'O mandato de quem venceu em 2024 foi cassado. Na eleição suplementar de 25/10/2026, o mais votado, Claudião Damacena, teve os votos anulados em decisão ainda sob recurso, e o TSE não registra eleito. Até a decisão final, a prefeitura é exercida interinamente pelo presidente da Câmara Municipal.']
# (C) eleito afastado; nova eleição em 06/12/2026 (calendário de eleições suplementares do TSE)
for code in (3109303, 3126703, 3127909, 3160504, 3512308):
    n, uf = MUN[code]; rec = munout[uf][code]
    rec['ex'] = ['supl', 'Quem venceu em 2024 foi afastado pela Justiça Eleitoral. Uma nova eleição está marcada para 06/12/2026 (calendário do TSE); até a posse, a prefeitura é exercida pelo presidente da Câmara Municipal.']
    stats['suplementar_pendente'] += 1
# (D) cassados que voltaram ao cargo por decisão judicial, com a eleição suplementar suspensa ou cancelada
r1, r2 = mrow(1508100, 'PREFEITO', '15'), mrow(1508100, 'VICE-PREFEITO', '15')
munout['PA'][1508100].update({'p': P(r1), 'v': P(r2), 'el': '06/10/2024', 'sup': 0, 't2': 0,
    'ex': ['jud', 'Alexandre Siqueira teve o mandato cassado pela Justiça Eleitoral, mas voltou ao cargo em julho de 2025 por decisão do STF (ministro Gilmar Mendes), que suspendeu a eleição suplementar marcada para 03/08/2025.']})
stats['prefeitos'] += 1; stats['suplementar_pendente'] -= 1
munout['PA'][1502103]['ex'] = ['jud', 'Teve o mandato cassado em 2025, mas o TSE determinou que o prefeito e o vice reassumissem os cargos; a eleição suplementar marcada para 03/08/2025 não foi realizada.']
munout['RS'][4323002]['ex'] = ['jud', 'Teve o mandato cassado, mas voltou ao cargo em março de 2026 por decisão do TSE, que cancelou a eleição suplementar marcada para 12/04/2026.']
munout['PA'][1504901]['ex'] = ['jud', 'O TRE-PA cassou o mandato em junho de 2025 e marcou eleição suplementar para 05/10/2025, mas a eleição foi suspensa (calendário do TSE) e não houve nova votação. O caso segue na Justiça.']
stats['suplementar_pendente'] -= 3
# (E) morte no cargo
munout['MG'][3106200]['ex'] = ['vice', 'Fuad Noman morreu em 26 de março de 2025, durante o mandato. Desde então, Álvaro Damião é o prefeito.']
# quem foi afastado sai do campo "prefeito" e fica registrado como "eleito em 2024, afastado"
for uf, D in munout.items():
    for code, rec in D.items():
        if (rec.get('ex') or [''])[0] == 'supl' and rec.get('p'):
            rec['af'] = rec.pop('p'); rec['afv'] = rec.pop('v', None); stats['prefeitos'] -= 1
print(dict(stats))
# ---------------- estados ----------------
EST = {s: (c, n, reg) for c, s, n, reg in G['estados']}
def eleitos(R, cargo, uf=None):
    return [r for r in R if r['DS_CARGO'] == cargo and r['DS_SIT_TOT_TURNO'] in ELEITO and (uf is None or r['SG_UF'] == uf)]
src = open(f'{SC}/aquarela-indices.html', encoding='utf-8').read()
def dsrows(kind):
    m = re.search(kind + r":\{title:.*?items:rank\(rows\(\"([^\"]*)\"", src, re.S)
    return [x.split('|') for x in m.group(1).split(';')]
DS = {k: dsrows(k) for k in ('camara', 'senado', 'gov')}
def pk(kind, uf, n):
    k = f'{kind}|{uf}|{n}'; return k if k in PF else ''
dep_now = json.load(open('/tmp/mapa/dep_atuais.json')); sen_now = json.load(open('/tmp/mapa/sen_atuais.json'))
def c26(nome_urna, uf):
    L = [r for r in R26 if r['NM_URNA_CANDIDATO'] == nome_urna and r['SG_UF'] == uf]; return P(L[0]) if L else None
# governo estadual: situações que o cruzamento de candidaturas não capta (verificadas em 29/10/2026)
GOVFIX = {
  'AM': (['ind', 'Wilson Lima e o vice, Tadeu de Souza, renunciaram em 5 de abril de 2026 para disputar a eleição. Em 4 de maio, a Assembleia Legislativa elegeu de forma indireta Roberto Cidade (União) e Serafim Corrêa (PSB) para completar o mandato, até 5 de janeiro de 2027.'],
         {'tit': c26('ROBERTO CIDADE', 'AM'), 'vice': ['Serafim Corrêa', 'Serafim Corrêa', 'PSB', '', 'M', '', '']}),
  'RR': (['int', 'Antonio Denarium renunciou em 27 de março de 2026 para disputar o Senado, e o vice, Edilson Damião, assumiu. Em 30 de abril, o TSE anulou a eleição de 2022 da chapa, afastou Damião e mandou fazer nova eleição. Desde então, o presidente da Assembleia Legislativa, Soldado Sampaio (Republicanos), é o governador interino. Na eleição suplementar de 21 de junho, Arthur Henrique (PL) foi o mais votado, mas disputou sub judice e não foi proclamado eleito.'],
         {'tit': c26('SOLDADO SAMPAIO', 'RR'), 'vice': None}),
  'RJ': (['int', 'Cláudio Castro renunciou em março de 2026, um dia antes de o TSE declará-lo inelegível. O vice, Thiago Pampolha, já havia deixado o cargo em maio de 2025 para assumir vaga no Tribunal de Contas do Estado, e o presidente da Assembleia Legislativa estava afastado do cargo. Por isso, o governo é exercido interinamente pelo presidente do Tribunal de Justiça, desembargador Ricardo Couto, situação mantida pelo STF.'],
         {'tit': ['Ricardo Couto', 'Ricardo Couto', '', '', 'M', '', 'Desembargador, presidente do Tribunal de Justiça'], 'vice': None}),
  'DF': (['vice', 'Ibaneis Rocha renunciou em março de 2026, de olho na disputa pelo Senado. Desde então, Celina Leão é a governadora, e o cargo de vice está vago.'], None),
}
# votos dos deputados estaduais/distritais eleitos: 2022 (arquivo de votação por município e zona do TSE) e 2026 (sistema de resultados do TSE)
_d26 = json.load(open('/tmp/mapa/res/de26.json'))
DE26 = {uf: {nr: [x[0], round(float(x[1].replace(',', '.')), 2)] for nr, x in d['el'].items()} for uf, d in _d26.items()}
_d22 = json.load(open('/tmp/mapa/res/de22.json'))
DE22 = {uf: {nr: [x[0], round(100 * x[0] / d['vv'], 2)] for nr, x in d['el'].items()} for uf, d in _d22.items()}
estados = {}
for uf, (cod, nome, reg) in EST.items():
    E = {'uf': uf, 'n': nome, 'cap': CAPS.get(uf)}
    # governador atual (eleito em 2022) e quem exerce hoje
    g22 = eleitos(R22, 'GOVERNADOR', uf); g = g22[-1] if g22 else None
    v22 = [r for r in eleitos(R22, 'VICE-GOVERNADOR', uf) if g and r['NR_CANDIDATO'] == g['NR_CANDIDATO']]; v = v22[-1] if v22 else None
    at = {'tit': P(g) if g else None, 'vice': P(v) if v else None}
    if g:
        c26 = cand26.get(TIT(g) or '-') or []
        outros = [r for r in c26 if r['DS_CARGO'] != 'GOVERNADOR']
        if outros:
            cv = [r for r in (cand26.get(TIT(v) or '-') or []) if r['DS_CARGO'] not in ('GOVERNADOR',)] if v else []
            if cv:
                at['ex'] = ['camara', f'{at["tit"][0]} renunciou para disputar a eleição de 2026 ({outros[0]["DS_CARGO"].lower()}), e {at["vice"][0]} também ({cv[0]["DS_CARGO"].lower()}). Pela lei, o governo passa ao presidente da Assembleia Legislativa.']
            else:
                at['ex'] = ['vice', f'{at["tit"][0]} renunciou em abril de 2026 para disputar a eleição de 2026 ({outros[0]["DS_CARGO"].lower()}). Desde então, {at["vice"][0]} é {"a governadora" if at["vice"][4]=="F" else "o governador"} em exercício.']
    if uf in GOVFIX: at['ex'], at['exer'] = GOVFIX[uf]
    g26 = [x for x in DS['gov'] if x[0] == uf][0]
    gr = [r for r in eleitos(R26, 'GOVERNADOR', uf)]; gv = [r for r in eleitos(R26, 'VICE-GOVERNADOR', uf) if gr and r['NR_CANDIDATO'] == gr[-1]['NR_CANDIDATO']]
    novo = {'tit': P(gr[-1]) if gr else [g26[1], '', g26[2], '', 'M', pk('gov', uf, g26[1]), ''], 'vice': P(gv[-1]) if gv else None}
    if novo['tit']: novo['tit'][0] = g26[1]; novo['tit'][5] = pk('gov', uf, g26[1]) or novo['tit'][5]
    E['gov'] = {'atual': at, 'novo': novo}
    # senadores
    sa = []
    for cod_, nm, full, part, u, sexo, part_, ini, fim, titular in sen_now:
        if u != uf: continue
        obs = f'Suplente em exercício no lugar de {titular}' if part_ != 'Titular' and titular else ''
        obs = (obs + '; ' if obs else '') + f'mandato até {fim[:4]}' if fim else obs
        sa.append([nm, full, part, '', 'F' if sexo.startswith('F') else 'M', sen2key.get(int(cod_), ''), obs])
    sn = []
    for x in DS['senado']:
        if x[0] != uf: continue
        sub = x[5][4:] if len(x) > 5 and x[5].startswith('sub:') else ''
        k = pk('senado', uf, x[1]); i = IDENT.get(k, {})
        obs = 'eleito em 2026' if x[3] else ('mandato até 2031' + (f'; assume no lugar de {sub}' if sub else ''))
        sn.append([x[1], tc(i.get('nome', '')), x[2], i.get('num', ''), 'F' if i.get('gen', '').startswith('FEM') else 'M', k, obs])
    E['sen'] = {'atual': sorted(sa, key=lambda p: nrm(p[0])), 'novo': sn}
    # deputados federais
    da = sorted([[n, '', p, '', 'M', cam2key.get(i, ''), ''] for i, n, p, u in dep_now if u == uf], key=lambda p: nrm(p[0]))
    dn = []
    for x in DS['camara']:
        if x[0] != uf: continue
        k = pk('camara', uf, x[1]); i = IDENT.get(k, {})
        dn.append([x[1], tc(i.get('nome', '')), x[2], i.get('num', ''), 'F' if i.get('gen', '').startswith('FEM') else 'M', k, ''])
    E['df'] = {'atual': da, 'novo': dn}
    # deputados estaduais / distritais
    cg = 'DEPUTADO DISTRITAL' if uf == 'DF' else 'DEPUTADO ESTADUAL'
    def comv(L, V):  # acrescenta [votos, % dos votos válidos no estado] (resultados do TSE)
        for x in L:
            v = V.get(x[3])
            if v: x += [v[0], v[1]]
        return L
    E['de'] = {'atual': comv(sorted((P(r) for r in eleitos(R22, cg, uf)), key=lambda p: (p[2], nrm(p[0]))), DE22.get(uf, {})),
               'novo': comv(sorted((P(r) for r in eleitos(R26, cg, uf)), key=lambda p: (p[2], nrm(p[0]))), DE26.get(uf, {}))}
    E['cg'] = 'distrital' if uf == 'DF' else 'estadual'
    E['nmun'] = len(munout.get(uf, {}))
    if E['cap'] and E['cap'] in munout.get(uf, {}):
        c = munout[uf][E['cap']]; E['capdata'] = {k: c[k] for k in ('p', 'v', 'ex', 'el', 'sup', 't2', 'af') if c.get(k) is not None}
    E['mun'] = {c: {'n': MUN[c][0], **{k: v for k, v in m.items() if k not in ('ver', 'vsup')}} for c, m in munout.get(uf, {}).items()}
    if uf == 'PE': E['noronha'] = 2605459
    estados[uf] = E
    if munout.get(uf): dump(f'ver-{uf}.json', {c: [m.get('ver', []), m.get('vsup', '')] for c, m in munout[uf].items()})
# ---------------- nacional ----------------
pres26 = [r for r in R26 if r['DS_CARGO'] == 'PRESIDENTE' and r['DS_SIT_TOT_TURNO'] == 'ELEITO']
vp26 = [r for r in R26 if r['DS_CARGO'] == 'VICE-PRESIDENTE' and r['DS_SIT_TOT_TURNO'] == 'ELEITO']
pres22 = [r for r in R22 if r['DS_CARGO'] == 'PRESIDENTE' and r['DS_SIT_TOT_TURNO'] == 'ELEITO']
vp22 = [r for r in R22 if r['DS_CARGO'] == 'VICE-PRESIDENTE' and r['DS_SIT_TOT_TURNO'] == 'ELEITO']
def pp(r, kind):
    x = P(r); x[5] = x[5] or ''
    return x
BR = {'pres': {'atual': {'tit': pp(pres22[-1], 'pres'), 'vice': pp(vp22[-1], 'pres')}, 'novo': {'tit': pp(pres26[-1], 'pres'), 'vice': pp(vp26[-1], 'pres')}},
      'uf': {uf: {'n': E['n'], 'gov_atual': ((E['gov']['atual'].get('exer') or {}).get('tit') or (E['gov']['atual']['vice'] if E['gov']['atual'].get('ex', [''])[0] == 'vice' else E['gov']['atual']['tit'])),
                  'gov_novo': E['gov']['novo']['tit'], 'nmun': E['nmun']} for uf, E in estados.items()},
      'tot': {'prefeitos': stats['prefeitos'], 'vereadores': stats['vereadores'], 'municipios': len(MUN) - 2,
              'dep_est_atual': sum(len(E['de']['atual']) for E in estados.values()), 'dep_est_novo': sum(len(E['de']['novo']) for E in estados.values())},
      'gerado': HOJE.strftime('%d/%m/%Y')}
dump('brasil.json', BR)
dump('municipios.json', [[c, n, uf] for c, (n, uf) in sorted(MUN.items(), key=lambda kv: nrm(kv[1][0]))])
# ---------------- geometria ----------------
br = json.loads(G['br'])
for f in br['features']:
    c = int(f['properties']['codarea']); s = [x for x in G['estados'] if x[0] == c][0]
    f['properties'] = {'c': c, 's': s[1], 'n': s[2]}
dump('geo-br.json', br)
for uf, txt in G['uf'].items():
    g = json.loads(txt)
    for f in g['features']:
        c = int(f['properties']['codarea']); f['properties'] = {'c': c, 'n': MUN[c][0]}
    dump(f'st-{uf}.json', {'d': estados[uf], 'g': g})  # dados do estado + mapa dos municípios num arquivo só
tam = sum(os.path.getsize(f'{OUT}/{f}') for f in os.listdir(OUT))
print('arquivos', len(os.listdir(OUT)), round(tam / 1e6, 1), 'MB')
print(json.dumps(BR['tot'], ensure_ascii=False), json.dumps(BR['pres'], ensure_ascii=False)[:300])
# depois deste script, rode mun/build_perf.py para gerar os perfis municipais (pf-*.json)
