// Coletor diário do Senado — rodar numa aba em https://legis.senado.leg.br
// Antes, defina: window.A='AAAA-MM-DD'; window.B='AAAA-MM-DD'; window.SENS=[códigos dos senadores com perfil]
// Resultado em window.OUT; progresso em window.ST
window.ST={fin:false,done:0,err:0};
(async()=>{
  const SS=new Set(SENS.map(Number));
  const SM=['Projeto de Lei Ordinária','Projeto de Lei Complementar','Proposta de Emenda à Constituição','Projeto de Decreto Legislativo','Projeto de Resolução','Proposta de Fiscalização e Controle'];
  const g=async u=>{ for(let k=0;k<6;k++){ try{ const r=await fetch(u,{headers:{Accept:'application/json'}}); if(r.status===404) return null; if(r.status===429){ await new Promise(r=>setTimeout(r,8000*(k+1))); continue; } if(!r.ok) throw r.status; return await r.json(); }catch(e){ await new Promise(r=>setTimeout(r,2000*(k+1))); } } ST.err++; return null; };
  const R={votacoes:[],processos:{}};
  const vs=(await g(`/dadosabertos/votacao?dataInicio=${A}&dataFim=${B}`))||[];
  for(const v of vs){ const c={Sim:0,'Não':0,'Abstenção':0}; (v.votos||[]).forEach(x=>{ if(x.siglaVotoParlamentar in c) c[x.siglaVotoParlamentar]++; });
    R.votacoes.push({k:`${v.codigoSessao}-${v.codigoSessaoVotacao}-${v.sequencialSessao}`,data:v.dataSessao,desc:v.descricaoVotacao||'',res:v.resultadoVotacao==='A'?'Aprovado':v.resultadoVotacao==='R'?'Rejeitado':(v.resultadoVotacao||''),sim:v.totalVotosSim??c.Sim,nao:v.totalVotosNao??c['Não'],abs:v.totalVotosAbstencao??c['Abstenção'],ident:v.identificacao||'',ementa:v.ementa||'',sec:v.votacaoSecreta==='S'?'Sim':'Não',votos:(v.votos||[]).filter(x=>SS.has(+x.codigoParlamentar)).map(x=>[x.codigoParlamentar,x.siglaVotoParlamentar||x.descricaoVotoParlamentar||''])}); }
  for(const cod of SENS){ const j=await g(`/dadosabertos/processo?codigoParlamentarAutor=${cod}`);
    if(Array.isArray(j)){ const rec=j.filter(p=>[p.dataApresentacao,p.dataSituacaoAtual,p.dataUltimaAtualizacao,p.dataDeliberacao].some(d=>(d||'').slice(0,10)>=A));
      if(rec.length) R.processos[cod]=rec.map(p=>{ const m=SM.includes(p.tipoDocumento); return [p.codigoMateria||p.id,p.identificacao||'',p.tipoDocumento||'',p.dataApresentacao||'',p.situacaoAtual||'',m?(p.ementa||''):(p.ementa||'').slice(0,180),/e outros/.test(p.autoria||'')?'e outros':'',p.normaGerada||'']; }); }
    ST.done++; await new Promise(r=>setTimeout(r,300)); }
  window.OUT=JSON.stringify(R); ST.fin=true; ST.tam=OUT.length;
})();
'iniciado'
