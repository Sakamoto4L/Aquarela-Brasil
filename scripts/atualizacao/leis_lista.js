// Leis (passo 1) — rodar numa aba em https://legis.senado.leg.br ; devolve a lista do ano (e do anterior até 15/jan)
const hoje=new Date(), Y=hoje.getFullYear(), anos=(hoje.getMonth()===0&&hoje.getDate()<=15)?[Y-1,Y]:[Y];
const g=async u=>{ for(let k=0;k<6;k++){ try{ const r=await fetch(u,{headers:{Accept:'application/json'}}); if(r.status===429){ await new Promise(r=>setTimeout(r,8000*(k+1))); continue; } if(!r.ok) throw r.status; return await r.json(); }catch(e){ await new Promise(r=>setTimeout(r,2000*(k+1))); } } throw new Error('falhou '+u); };
const L=[]; for(const t of ['LEI','LCP','LDL','EMC','EMR','DEL','MPV','CON']) for(const a of anos){ const j=await g(`/dadosabertos/legislacao/lista.json?tipo=${t}&ano=${a}`); const d=j.ListaDocumento.documentos&&j.ListaDocumento.documentos.documento; (d?(Array.isArray(d)?d:[d]):[]).forEach(x=>L.push([x.id,x.tipo,x.numero,x.dataassinatura,x.ementa,x.apelido])); }
'X'.repeat(120000)+'@@'+JSON.stringify(L)
