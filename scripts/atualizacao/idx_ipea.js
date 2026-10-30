// Índices — rodar numa aba em https://www.ipeadata.gov.br ; devolve ipea.json
const get=async s=>(await (await fetch(`/api/odata4/ValoresSerie(SERCODIGO='${s}')`)).json()).value.filter(x=>x.VALVALOR!=null).map(x=>[x.VALDATA.slice(0,10),x.VALVALOR]);
const real={}; for(const [d,v] of await get('GAC12_SALMINRE12')){ const y=d.slice(0,4); (real[y]=real[y]||[]).push([d,v]); }
const R={}; for(const [y,a] of Object.entries(real)) R[y]=[a.reduce((s,x)=>s+x[1],0)/a.length,a.length,a.map(x=>x[0]).sort().pop().slice(0,7)];
const nom={}; for(const [d,v] of await get('MTE12_SALMIN12')) nom[d.slice(0,4)]=v;
const dext={}; for(const [d,v] of await get('BM_DEXTEI')) dext[d.slice(0,4)]=v;
'X'.repeat(120000)+'@@'+JSON.stringify({real:R,nom,dext})
