// Coleta 2 da Câmara — mesma aba da coleta 1 (usa window.CAM1R)
window.CAM2={fin:false,done:0,tot:0,err:[]};
(async()=>{
  const g=async u=>{ for(let k=0;k<6;k++){ try{ const r=await fetch(u,{headers:{Accept:'application/json'}}); if(r.status===404) return null; if(!r.ok) throw r.status; return await r.json(); }catch(e){ await new Promise(r=>setTimeout(r,1500*(k+1))); } } CAM2.err.push(u); return null; };
  const pool=async(items,n,fn)=>{ let i=0; await Promise.all(Array.from({length:n},async()=>{ while(i<items.length){ const x=items[i++]; await fn(x); CAM2.done++; } })); };
  const A=CAM1R.janela[0], R={status:{},autores:{}};
  const novos=CAM1R.tramitadas.filter(t=>(t[4]||'')>=A).map(t=>t[0]);
  const todos=CAM1R.tramitadas.map(t=>t[0]);
  CAM2.tot=todos.length+novos.length;
  await pool(todos,6,async id=>{ const j=await g(`/api/v2/proposicoes/${id}`); if(j&&j.dados){ const d=j.dados; R.status[id]=[(d.statusProposicao||{}).descricaoSituacao||'',d.descricaoTipo||'',d.siglaTipo||'']; } });
  await pool(novos,6,async id=>{ const j=await g(`/api/v2/proposicoes/${id}/autores`); if(j&&j.dados){ const a=j.dados.filter(x=>/\/deputados\/\d+$/.test(x.uri||'')).map(x=>[+x.uri.split('/').pop(),x.ordemAssinatura]); if(a.length) R.autores[id]=a; } });
  window.CAM2R=R; CAM2.fin=true;
})();
'iniciado'
