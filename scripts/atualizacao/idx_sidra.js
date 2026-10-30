// Índices — rodar numa aba em https://servicodados.ibge.gov.br ; devolve sidra.json
const g=async u=>{ for(let k=0;k<5;k++){ try{ const r=await fetch(u); if(!r.ok) throw r.status; return await r.json(); }catch(e){ await new Promise(r=>setTimeout(r,2000*(k+1))); } } throw new Error('falhou '+u); };
const B='/api/v3/agregados', L='localidades=N1[all]';
const Q={ipca:`${B}/1737/periodos/-24/variaveis/69|2266?${L}`, cnt:`${B}/5932/periodos/-8/variaveis/6562?${L}&classificacao=11255[90707]`, cna:`${B}/6784/periodos/-4/variaveis/9810?${L}`, desM:`${B}/6381/periodos/-15/variaveis/4099?${L}`, desA:`${B}/4562/periodos/-3/variaveis/4099?${L}`, infA:`${B}/4708/periodos/-3/variaveis/12466?${L}`, gini:`${B}/7435/periodos/-3/variaveis/10681?${L}`, analf:`${B}/7113/periodos/-3/variaveis/10267?${L}&classificacao=2[6794]|58[2795]`};
const out={}; for(const [k,u] of Object.entries(Q)){ const v=await g(u); out[k]=Object.fromEntries(v.map(x=>[x.id,x.resultados[0].series[0].serie])); }
'X'.repeat(120000)+'@@'+JSON.stringify(out)
