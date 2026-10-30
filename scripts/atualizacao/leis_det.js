// Leis (passo 2) — mesma aba; defina antes window.IDS=[ids a detalhar]. Rode, depois consulte window.LD.fin e devolva 'X'.repeat(120000)+'@@'+window.LDOUT
window.LD={fin:false,done:0,err:0};
(async()=>{
  const g=async u=>{ for(let k=0;k<6;k++){ try{ const r=await fetch(u,{headers:{Accept:'application/json'}}); if(r.status===429){ await new Promise(r=>setTimeout(r,8000*(k+1))); continue; } if(!r.ok) throw r.status; return await r.json(); }catch(e){ await new Promise(r=>setTimeout(r,2000*(k+1))); } } LD.err++; return null; };
  const arr=x=>!x?[]:Array.isArray(x)?x:[x]; const out={};
  const pick=d=>{ const id=d.identificacao||{}; const vv=arr(d.vides&&d.vides.vide); const rev=vv.find(x=>/Revoga..o.*Norma no Todo/i.test(x.comentario||'')); const mp=vv.filter(x=>/convers|rejei|efic|prejudic|reedi/i.test(x.comentario||'')).map(x=>[x.comentario,x.nomeNormaPosterior]).slice(0,6); let cl=d.classes&&d.classes.classe; if(Array.isArray(cl)) cl=cl.join(' ;; '); let cat=d.catalogo&&d.catalogo.frase; if(Array.isArray(cat)) cat=cat.join(' ;; '); const ed=arr(d.edivs&&d.edivs.ediv).filter(x=>/Revoga..o.*Norma no Todo/i.test(x.comentario||'')).map(x=>[x.codnormaAnterior,id.normaNome]); return [id.situacao||'',rev?rev.nomeNormaPosterior:'',(typeof d.observacao==='string'?d.observacao:'').slice(0,300),cl||'',cat||'',mp,ed]; };
  let i=0; await Promise.all(Array.from({length:4},async()=>{ while(i<IDS.length){ const x=IDS[i++]; const j=await g(`/dadosabertos/legislacao/${x}.json`); if(j){ let d=j.DetalheDocumento.documentos.documento; d=Array.isArray(d)?d[0]:d; out[x]=pick(d); } LD.done++; await new Promise(r=>setTimeout(r,250)); } }));
  window.LDOUT=JSON.stringify(out); LD.fin=true;
})();
'iniciado'
