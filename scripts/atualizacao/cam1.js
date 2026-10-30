// Coleta 1 da Câmara — rodar numa aba em https://dadosabertos.camara.leg.br (defina A e B antes: window.A='AAAA-MM-DD'; window.B='AAAA-MM-DD')
window.CAM1={fin:false,err:[],log:[]};
(async()=>{
  const g=async u=>{ for(let k=0;k<6;k++){ try{ const r=await fetch(u,{headers:{Accept:'application/json'}}); if(r.status===404) return null; if(!r.ok) throw r.status; return await r.json(); }catch(e){ await new Promise(r=>setTimeout(r,1500*(k+1))); } } CAM1.err.push(u); return null; };
  const pages=async u=>{ const out=[]; let url=u; while(url){ const j=await g(url); if(!j) break; out.push(...j.dados); const nx=(j.links||[]).find(l=>l.rel==='next'); url=nx?nx.href.replace(/^https?:\/\/[^/]+/,''):null; } return out; };
  const pool=async(items,n,fn)=>{ let i=0; await Promise.all(Array.from({length:n},async()=>{ while(i<items.length){ const x=items[i++]; await fn(x); } })); };
  const R={janela:[A,B],votacoes:[],exercicio:[],tramitadas:[]};
  // deputados em exercício hoje
  R.exercicio=(await pages('/api/v2/deputados?itens=1000')).map(d=>d.id);
  // votações no período (dia a dia evita o limite de 3 meses e páginas grandes)
  const vs=await pages(`/api/v2/votacoes?dataInicio=${A}&dataFim=${B}&itens=200&ordem=ASC&ordenarPor=dataHoraRegistro`);
  CAM1.log.push('votacoes '+vs.length);
  await pool(vs,4,async v=>{
    const vv=await g(`/api/v2/votacoes/${v.id}/votos`); const votos=(vv&&vv.dados)||[];
    if(!votos.length) return;
    const d=await g(`/api/v2/votacoes/${v.id}`); const dd=(d&&d.dados)||{};
    const af=(dd.proposicoesAfetadas&&dd.proposicoesAfetadas.length?dd.proposicoesAfetadas:(dd.objetosPossiveis||[])).slice(0,3).map(p=>[`${p.siglaTipo} ${p.numero}/${p.ano}`,(p.ementa||'').slice(0,400),String(p.id)]);
    const c={Sim:0,'Não':0,out:0}; votos.forEach(x=>{ if(x.tipoVoto==='Sim') c.Sim++; else if(x.tipoVoto==='Não') c['Não']++; else c.out++; });
    R.votacoes.push({id:v.id,data:v.data,org:v.siglaOrgao,desc:v.descricao||'',aprov:v.aprovacao==null?'':String(v.aprovacao),sim:c.Sim,nao:c['Não'],out:c.out,props:af,votos:votos.map(x=>[x.deputado_.id,x.tipoVoto,x.deputado_.siglaPartido||''])});
  });
  CAM1.log.push('nominais '+R.votacoes.length);
  // proposições que tramitaram no período
  const ps=await pages(`/api/v2/proposicoes?dataInicio=${A}&dataFim=${B}&itens=100&ordem=ASC&ordenarPor=id`);
  R.tramitadas=ps.map(p=>[p.id,p.siglaTipo,p.numero,p.ano,(p.dataApresentacao||'').slice(0,10),p.ementa||'']);
  CAM1.log.push('tramitadas '+R.tramitadas.length);
  window.CAM1R=R; CAM1.fin=true;
})();
'iniciado'
