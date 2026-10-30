// Índices — rodar numa aba em https://olinda.bcb.gov.br ; devolve focus.json
const Y=new Date().getFullYear(); const out={};
for(const ind of ['IPCA','PIB Total']) for(const y of [Y-1,Y,Y+1]){ const u=`/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais?$top=1&$filter=Indicador%20eq%20'${encodeURIComponent(ind)}'%20and%20DataReferencia%20eq%20'${y}'%20and%20baseCalculo%20eq%200&$orderby=Data%20desc&$format=json&$select=Data,Mediana`; const j=await (await fetch(u)).json(); out[ind+'|'+y]=j.value[0]||null; }
'X'.repeat(120000)+'@@'+JSON.stringify(out)
