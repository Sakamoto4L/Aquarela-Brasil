// Coletor diário da Câmara. Rodar numa aba em https://dadosabertos.camara.leg.br
// Antes, defina: window.A='AAAA-MM-DD' (início da janela); window.B='AAAA-MM-DD' (hoje); window.DEP=[ids dos deputados com perfil]
// Resultado em window.OUT (string JSON); progresso em window.ST
window.ST={fin:false,fase:'',done:0,tot:0,err:0};
(async()=>{
  const DS=new Set(DEP.map(Number));
  const g=async u=>{ for(let k=0;k<6;k++){ try{ const r=await fetch(u,{headers:{Accept:'application/json'}}); if(r.status===404) return null; if(!r.ok) throw r.status; return await r.json(); }catch(e){ await new Promise(r=>setTimeout(r,1500*(k+1))); } } ST.err++; return null; };
  const pages=async u=>{ const out=[]; let url=u; while(url){ const j=await g(url); if(!j) break; out.push(...j.dados); const nx=(j.links||[]).find(l=>l.rel==='next'); url=nx?nx.href.replace(/^https?:\/\/[^/]+/,''):null; } return out; };
  const pool=async(items,n,fn)=>{ let i=0; await Promise.all(Array.from({length:n},async()=>{ while(i<items.length){ const x=items[i++]; await fn(x); ST.done++; } })); };
  const L=[],LI={}; const ix=s=>{ s=s||''; if(!(s in LI)){ LI[s]=L.length; L.push(s);} return LI[s]; };
  const R={janela:[A,B],exercicio:[],votacoes:[],L,st:[],novas:[]};
  ST.fase='votacoes';
  const vs=await pages(`/api/v2/votacoes?dataInicio=${A}&dataFim=${B}&itens=200&ordem=ASC&ordenarPor=dataHoraRegistro`);
  await pool(vs,4,async v=>{
    const vv=await g(`/api/v2/votacoes/${v.id}/votos`); const votos=(vv&&vv.dados)||[];
    if(!votos.length) return;
    const d=await g(`/api/v2/votacoes/${v.id}`); const dd=(d&&d.dados)||{};
    const af=(dd.proposicoesAfetadas&&dd.proposicoesAfetadas.length?dd.proposicoesAfetadas:(dd.objetosPossiveis||[])).slice(0,3).map(p=>[`${p.siglaTipo} ${p.numero}/${p.ano}`,(p.ementa||'').slice(0,400),String(p.id)]);
    const c={s:0,n:0,o:0}; votos.forEach(x=>{ if(x.tipoVoto==='Sim') c.s++; else if(x.tipoVoto==='Não') c.n++; else c.o++; });
    R.votacoes.push({id:v.id,data:v.data,org:v.siglaOrgao,desc:v.descricao||'',aprov:v.aprovacao==null?'':String(v.aprovacao),sim:c.s,nao:c.n,out:c.o,props:af,votos:votos.filter(x=>DS.has(x.deputado_.id)).map(x=>[x.deputado_.id,x.tipoVoto,''])});
  });
  if(R.votacoes.some(v=>v.org==='PLEN')) R.exercicio=(await pages('/api/v2/deputados?itens=1000')).map(d=>d.id).filter(id=>DS.has(id));
  ST.fase='tramitadas';
  const ps=await pages(`/api/v2/proposicoes?dataInicio=${A}&dataFim=${B}&itens=100&ordem=ASC&ordenarPor=id`);
  ST.done=0; ST.tot=ps.length; ST.fase='situacoes';
  await pool(ps,6,async p=>{
    const j=await g(`/api/v2/proposicoes/${p.id}`); if(!j||!j.dados) return; const d=j.dados;
    const sit=ix((d.statusProposicao||{}).descricaoSituacao);
    R.st.push([p.id,sit]);
    if((p.dataApresentacao||'').slice(0,10)>=A){
      const a=await g(`/api/v2/proposicoes/${p.id}/autores`); const au=((a&&a.dados)||[]).filter(x=>/\/deputados\/\d+$/.test(x.uri||'')).map(x=>[+x.uri.split('/').pop(),x.ordemAssinatura]).filter(x=>DS.has(x[0]));
      if(au.length) R.novas.push([p.id,p.siglaTipo,p.numero,p.ano,(p.dataApresentacao||'').slice(0,10),p.ementa||'',sit,d.descricaoTipo||'',au]);
    }
  });
  window.OUT=JSON.stringify(R); ST.fin=true; ST.tam=OUT.length;
})();
'iniciado'
