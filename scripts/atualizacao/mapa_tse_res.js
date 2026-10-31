// Mapa — rodar numa aba em https://resultados.tse.jus.br ; devolve a lista oficial de pleitos e eleições do sistema de resultados → W/in/mapa_tse_res.json
// Formato: [[pleito, data, ciclo, eleição, nome, abrangência], ...]
const j=await (await fetch('/oficial/comum/config/ele-c.json',{cache:'no-store'})).json();
const L=[]; for(const p of j.pl) for(const e of p.e) L.push([p.cd,p.dt,p.c,e.cd,e.nm,(e.abr||[]).map(a=>a.cd+(a.mu?':'+a.mu.map(m=>m.cd||m).join('|'):'')).join(',')]);
'X'.repeat(150000)+'@@'+JSON.stringify(L)
