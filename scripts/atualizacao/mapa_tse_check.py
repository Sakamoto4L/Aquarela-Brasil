# mapa_tse_check.py — conferência diária do TSE para a aba Mapa (governos e prefeituras).
# Compara o calendário oficial de eleições suplementares e a lista de eleições do sistema de resultados do TSE com a referência
# já refletida no site (data/mapa/tse_ref.json). Se nada mudou, a conferência do TSE vale para hoje.
# uso: python3 -I mapa_tse_check.py <tse_ref.json> <mapa_tse_cal.json> <mapa_tse_res.json> <meta.json de entrada> <pasta_saida> [DD/MM/AAAA]
# Saída em <pasta_saida>: meta.json (com "tse" = hoje só se não houver novidade). Imprime as novidades.
# Código de saída 0 = sem novidade; 3 = há novidade no TSE: o Mapa precisa de revisão (a referência NÃO é atualizada; avise o usuário).
# Para gerar a referência depois de revisar o Mapa: acrescente --nova-ref (grava <pasta_saida>/tse_ref.json com o estado atual).
import json, sys, os, datetime
REF, CAL, RES, META_IN, OUT = sys.argv[1:6]
args = [a for a in sys.argv[6:] if not a.startswith('--')]
try:
    from zoneinfo import ZoneInfo; HOJE = datetime.datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y')
except Exception: HOJE = datetime.date.today().strftime('%d/%m/%Y')
if args: HOJE = args[0]
os.makedirs(OUT, exist_ok=True)
cal = json.load(open(CAL, encoding='utf-8')); res = json.load(open(RES, encoding='utf-8'))
if not isinstance(res, list) or len(res) < 10 or not any(cal.get(k) for k in cal): sys.exit('ERRO: dados do TSE incompletos; nada foi alterado')
cur = {'cal': sorted(['|'.join(map(str, r)) for k, v in cal.items() if v for r in v]),
       'res': sorted(['|'.join(map(str, r)) for r in res])}
meta = json.load(open(META_IN, encoding='utf-8')) if os.path.exists(META_IN) else {}
if '--nova-ref' in sys.argv:
    json.dump(cur, open(os.path.join(OUT, 'tse_ref.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    meta['tse'] = HOJE
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(json.dumps({'nova_referencia': True, 'meta': meta}, ensure_ascii=False)); sys.exit(0)
ref = json.load(open(REF, encoding='utf-8'))
# o calendário do ano anterior pode sair da coleta em janeiro: compare só os anos coletados
anos = {k for k, v in cal.items() if v}
def ano(x):
    d = x.split('|')[1]; return d[-4:] if len(d) >= 4 else ''
novo_cal = [x for x in cur['cal'] if x not in ref['cal']]
sumiu_cal = [x for x in ref['cal'] if x not in cur['cal'] and ano(x) in anos]
novo_res = [x for x in cur['res'] if x not in ref['res']]
sumiu_res = [x for x in ref['res'] if x not in cur['res']]
nov = {'calendario_novo': novo_cal, 'calendario_removido': sumiu_cal, 'resultados_novo': novo_res, 'resultados_removido': sumiu_res}
tem = any(nov.values())
if not tem: meta['tse'] = HOJE
json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(json.dumps({'novidades': tem, **nov, 'meta': meta}, ensure_ascii=False, indent=1))
sys.exit(3 if tem else 0)
