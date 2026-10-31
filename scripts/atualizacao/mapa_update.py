# mapa_update.py — confere na aba Mapa os deputados federais e senadores EM EXERCÍCIO (Câmara e Senado) e regrava só os estados que mudaram.
# uso: python3 -I mapa_update.py <pasta_mapa_com_st-UF.json> <perfis.json> <mapa_cam.json> <mapa_sen.json> <saida_dir> [DD/MM/AAAA]
# Grava em <saida_dir> os st-UF.json alterados e meta.json ({"parl":"DD/MM/AAAA","tse":"..."}); imprime as mudanças.
# Prefeitos, vices, vereadores e governadores (TSE) NÃO são recalculados aqui.
import json, sys, os, re, unicodedata, datetime
D, PFF, CAMF, SENF, OUT = sys.argv[1:6]
try:
    from zoneinfo import ZoneInfo; HOJE = datetime.datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y')
except Exception: HOJE = datetime.date.today().strftime('%d/%m/%Y')
if len(sys.argv) > 6: HOJE = sys.argv[6]
os.makedirs(OUT, exist_ok=True)
def nrm(s):
    s = unicodedata.normalize('NFD', s or ''); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').upper()
    return re.sub(r'\s+', ' ', re.sub(r"[^A-Z0-9 ]", ' ', s)).strip()
PF = json.load(open(PFF, encoding='utf-8'))['perf']
cam2key = {int(v['cam']['id']): k for k, v in PF.items() if v.get('cam')}
sen2key = {int(v['sen']['cod']): k for k, v in PF.items() if v.get('sen')}
dep_now = json.load(open(CAMF, encoding='utf-8')); sen_now = json.load(open(SENF, encoding='utf-8'))
if len(dep_now) < 400 or len(sen_now) < 70: sys.exit(f'ERRO: listas incompletas (deputados {len(dep_now)}, senadores {len(sen_now)}); nada foi alterado')
meta_p = os.path.join(D, 'meta.json'); META = json.load(open(meta_p)) if os.path.exists(meta_p) else {'tse': '29/10/2026'}
mud = []; nst = 0
for f in sorted(os.listdir(D)):
    m = re.fullmatch(r'st-([A-Z]{2})\.json', f)
    if not m: continue
    uf = m.group(1); S = json.load(open(os.path.join(D, f), encoding='utf-8')); E = S['d']
    sa = []
    for cod_, nm, full, part, u, sexo, part_, ini, fim, titular in sen_now:
        if u != uf: continue
        obs = f'Suplente em exercício no lugar de {titular}' if part_ != 'Titular' and titular else ''
        obs = (obs + '; ' if obs else '') + f'mandato até {fim[:4]}' if fim else obs
        sa.append([nm, full, part, '', 'F' if sexo.startswith('F') else 'M', sen2key.get(int(cod_), ''), obs])
    sa = sorted(sa, key=lambda p: nrm(p[0]))
    da = sorted([[n, '', p, '', 'M', cam2key.get(i, ''), ''] for i, n, p, u in dep_now if u == uf], key=lambda p: nrm(p[0]))
    ch = False
    for lab, key, new in (('senado', 'sen', sa), ('câmara', 'df', da)):
        old = E.get(key, {}).get('atual', [])
        if old != new:
            ch = True
            on = {(x[0], x[2]) for x in old}; nn = {(x[0], x[2]) for x in new}
            sai = sorted(on - nn); ent = sorted(nn - on)
            det = []
            if ent: det.append('entra ' + ', '.join(f'{a} ({b})' for a, b in ent))
            if sai: det.append('sai ' + ', '.join(f'{a} ({b})' for a, b in sai))
            if not det: det.append('observações/perfis atualizados')
            mud.append(f'{uf} {lab}: ' + '; '.join(det))
            E.setdefault(key, {})['atual'] = new
    if ch:
        nst += 1
        json.dump(S, open(os.path.join(OUT, f), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
META['parl'] = HOJE; META.setdefault('tse', '29/10/2026')
json.dump(META, open(os.path.join(OUT, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(json.dumps({'estados_alterados': nst, 'mudancas': mud, 'meta': META}, ensure_ascii=False, indent=1))
