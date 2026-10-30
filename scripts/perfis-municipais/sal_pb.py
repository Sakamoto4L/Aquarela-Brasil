# sal_pb.py — salário pago a prefeitos, vices e vereadores da Paraíba, a partir da folha enviada ao TCE-PB (SAGRES, dados abertos 2026).
# Devolve {(município normalizado, nome normalizado): [valor mensal mais frequente em 2026, último mês, cargo na folha]}.
import csv, collections, re, unicodedata
def nrm(s):
    s = unicodedata.normalize('NFD', s or ''); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').upper()
    return re.sub(r'\s+', ' ', re.sub(r"[^A-Z0-9 ]", ' ', s)).strip()
def val(s): return float(s.replace('.', '').replace(',', '.'))
def load(path='/tmp/pb/servidores-2026.csv'):
    P = collections.defaultdict(list)
    for r in csv.DictReader(open(path, encoding='utf-8-sig'), delimiter=';'):
        if r['tipo_cargo'] != 'Eletivos': continue
        cg = nrm(r['descricao_cargo'].split(' - ', 1)[-1]).replace(' ', '')
        if 'CONSELH' in cg: continue
        k = 'P' if cg.startswith('PREFEIT') else 'VP' if cg.startswith('VICE') else 'V' if 'VEREAD' in cg or cg in ('PRESIDENTE',) else None
        if not k: continue
        P[(nrm(r['nome_municipio']), nrm(r['nome_servidor']))].append((r['ano_mes'], k, val(r['valor_vantagem'])))
    out = {}
    for key, L in P.items():
        L.sort(); last = L[-1]; same = [v for m, k, v in L if k == last[1] and v > 0]
        if not same: continue
        c = collections.Counter(round(v, 2) for v in same).most_common()
        top = max(c, key=lambda x: (x[1], x[0]))[0]   # valor mais frequente (em empate, o maior)
        out[key] = [top, last[0], last[1]]
    return out
if __name__ == '__main__':
    o = load(); print(len(o)); import itertools
    for k, v in itertools.islice(o.items(), 5): print(k, v)
    print([ (k,v) for k,v in o.items() if k[0]=='JOAO PESSOA' and v[2]!='V'])
