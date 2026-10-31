// Mapa — rodar numa aba em https://legis.senado.leg.br ; devolve senadores em exercício → W/in/mapa_sen.json
// formato: [codigo, nome, nome completo, partido, uf, sexo, participacao, inicio, fim do mandato, nome do titular]
const j=await (await fetch('/dadosabertos/senador/lista/atual.json',{headers:{Accept:'application/json'}})).json();
let P=j.ListaParlamentarEmExercicio.Parlamentares.Parlamentar; if(!Array.isArray(P)) P=[P];
'X'.repeat(150000)+'@@'+JSON.stringify(P.map(p=>{const I=p.IdentificacaoParlamentar,M=p.Mandato||{};const L2=M.SegundaLegislaturaDoMandato||{},L1=M.PrimeiraLegislaturaDoMandato||{};
 return [I.CodigoParlamentar,I.NomeParlamentar,I.NomeCompletoParlamentar,I.SiglaPartidoParlamentar,I.UfParlamentar,I.SexoParlamentar||'',M.DescricaoParticipacao||'',L1.DataInicio||'',L2.DataFim||L1.DataFim||'',(M.Titular||{}).NomeParlamentar||''];}))
