# leis_plan.py — decide quais normas detalhar hoje. uso: python3 -I leis_plan.py <pasta data/leis> <lista.json> <pendentes.json>
import json, sys
D, LI, PE = sys.argv[1:4]
ids = {e[0] for f in ('leis', 'del', 'mpv', 'dpl') for e in json.load(open(f'{D}/{f}.json'))}
novos = [int(x[0]) for x in json.load(open(LI)) if int(x[0]) not in ids]
pe = json.load(open(PE))
det = list(dict.fromkeys(novos + pe['mp_abertas'] + pe['sem_situacao'][:600]))
print('IDS=' + json.dumps(det, separators=(',', ':')))
print(f'# {len(novos)} novas, {len(pe["mp_abertas"])} MPs em aberto, {min(600, len(pe["sem_situacao"]))} sem situação')
