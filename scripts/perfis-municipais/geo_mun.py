# geo_mun.py — contorno simplificado de todos os municípios (só para desenhar as divisões no mapa do Brasil)
import json, os, math
D = '/tmp/claude-0/-home-claude/09aefdc5-706f-5d9c-918a-28b3af6171a1/scratchpad/site/data/mapa'
TOL = float(os.environ.get('TOL', '0.008'))
def dp(pts, tol):
    if len(pts) < 3: return pts
    keep = [False]*len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts)-1)]
    while st:
        a, b = st.pop(); (x1, y1), (x2, y2) = pts[a], pts[b]; dx, dy = x2-x1, y2-y1; L = math.hypot(dx, dy) or 1e-12
        md, mi = 0, -1
        for i in range(a+1, b):
            x, y = pts[i]; d = abs(dy*x - dx*y + x2*y1 - y2*x1)/L
            if d > md: md, mi = d, i
        if md > tol: keep[mi] = True; st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]
def ring(r):
    k = max(range(len(r)), key=lambda i: (r[i][0]-r[0][0])**2 + (r[i][1]-r[0][1])**2)
    q = dp(r[:k+1], TOL) + dp(r[k:], TOL)[1:]; q = [[round(x, 2), round(y, 2)] for x, y in q]
    out = [q[0]] + [p for i, p in enumerate(q[1:]) if p != q[i]]
    return out if len(out) >= 4 else None
feats = []
for f in sorted(os.listdir(D)):
    if not f.startswith('st-') or f == 'st-DF.json': continue
    for ft in json.load(open(f'{D}/{f}'))['g']['features']:
        g = ft['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        P = []
        for poly in polys:
            r = ring(poly[0])
            if r: P.append([r])
        if P: feats.append({'type': 'Feature', 'properties': {'name': 'm' + str(ft['properties'].get('c', ''))}, 'geometry': {'type': 'MultiPolygon', 'coordinates': P}})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(f'{D}/geo-mun.json', 'w'), separators=(',', ':'))
print(len(feats), os.path.getsize(f'{D}/geo-mun.json'))
