// Mapa — rodar numa aba em https://www.tse.jus.br (qualquer página do portal) ; devolve o calendário oficial de eleições suplementares
// (ano atual e seguinte) → W/in/mapa_tse_cal.json
// Formato: {"AAAA": [[tabela, data, TRE, município/UF, resolução], ...]} — tabela 0 = prefeito e vice; as outras = vereador, governador, consulta.
const Y=new Date().getFullYear(); const out={};
for(const y of [Y,Y+1]){ const r=await fetch(`/eleicoes/eleicoes-suplementares/calendarios/calendario-das-eleicoes-suplementares-${y}`); if(!r.ok){ out[y]=null; continue; }
  const d=new DOMParser().parseFromString(await r.text(),'text/html'); const L=[];
  d.querySelectorAll('table').forEach((t,ti)=>t.querySelectorAll('tr').forEach(tr=>{ const c=[...tr.cells].map(x=>x.textContent.replace(/\s+/g,' ').trim()); if(c.length>=4&&c[0]&&!/^data$/i.test(c[0])) L.push([ti,c[0],c[1],c[2],c[3]]); }));
  out[y]=L; }
'X'.repeat(150000)+'@@'+JSON.stringify(out)
