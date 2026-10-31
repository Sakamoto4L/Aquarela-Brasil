// Mapa — rodar numa aba em https://dadosabertos.camara.leg.br ; devolve deputados em exercício [id,nome,partido,uf] → W/in/mapa_cam.json
const j=await (await fetch('/api/v2/deputados?itens=1000',{headers:{Accept:'application/json'}})).json();
'X'.repeat(150000)+'@@'+JSON.stringify(j.dados.map(d=>[d.id,d.nome,d.siglaPartido,d.siglaUf]))
