// Índices — rodar numa aba em https://api.bcb.gov.br ; devolve bcb.json
const Y=new Date().getFullYear();
const g=async u=>{ for(let k=0;k<5;k++){ try{ const r=await fetch(u); if(!r.ok) throw r.status; return await r.json(); }catch(e){ await new Promise(r=>setTimeout(r,2000*(k+1))); } } throw new Error('falhou '+u); };
const rng=(s,a,b)=>g(`/dados/serie/bcdata.sgs.${s}/dados?formato=json&dataInicial=${a}&dataFinal=${b}`);
const out={selic:{},dol:{},dolm:{},meta:[],mens:{}};
for(const y of [Y-1,Y]){
  const s=await rng(11,`01/01/${y}`,`31/12/${y}`); let p=1; s.forEach(x=>p*=1+parseFloat(x.valor)/100);
  if(s.length) out.selic[y]={acc:(p-1)*100,n:s.length,first:s[0].data,last:s[s.length-1].data};
  const d=await rng(1,`01/01/${y}`,`31/12/${y}`); if(d.length){ const v=d.map(x=>parseFloat(x.valor)); out.dol[y]={avg:v.reduce((a,b)=>a+b,0)/v.length,n:v.length,first:d[0].data,last:d[d.length-1].data};
    const m={}; d.forEach(x=>{ const k=x.data.slice(6)+'-'+x.data.slice(3,5); (m[k]=m[k]||[]).push(parseFloat(x.valor)); }); for(const [k,a] of Object.entries(m)) out.dolm[k]=[a.reduce((s,b)=>s+b,0)/a.length,a.length]; }
}
const mt=await rng(432,`01/01/${Y-4}`,`31/12/${Y}`); const hoje=new Date(); let prev=null;
for(const x of mt){ const [dd,mm,yy]=x.data.split('/'); if(new Date(+yy,+mm-1,+dd)>hoje) break; if(x.valor!==prev){ out.meta.push([x.data,x.valor]); prev=x.valor; } }
for(const s of [4513,13762,5793,3546]) out.mens[s]=(await rng(s,`01/01/${Y-2}`,`31/12/${Y}`)).map(x=>[x.data,x.valor]);
'X'.repeat(120000)+'@@'+JSON.stringify(out)
