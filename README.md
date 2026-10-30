# Aquarela Brasil

Site de dados públicos sobre o Brasil, em uma única página (`index.html`) com quatro abas:

- **Mapa** — quem governa cada estado e cada município: governadores, senadores, deputados federais e estaduais, prefeitos, vices e vereadores, com perfil de cada político municipal (votação de 2024, histórico de candidaturas, bens declarados desde 2006 e salário, quando há fonte).
- **Governo** — deputados federais, senadores, governadores e presidente eleitos em 2026, com propostas, votações e trajetória.
- **Índices** — séries históricas oficiais (PIB, inflação, Selic, dólar, reservas, dívida, emprego, renda, população e outras).
- **Leis** — todas as normas federais com força de lei.

## Como abrir

A página carrega os dados da pasta `data/` por caminho relativo, então precisa ser servida por um servidor web:

```bash
python3 -m http.server 8000
# abra http://localhost:8000
```

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `index.html` | A página inteira (HTML, CSS e JavaScript). Os dados dos Índices ficam embutidos em `const D = {...}`. |
| `data/mapa/` | Mapa: geometrias (IBGE), quem governa cada estado (`st-UF.json`), vereadores (`ver-UF.json`), perfis municipais (`pf-0..7.json`) e divisões municipais simplificadas (`geo-mun.json`). |
| `data/p/`, `data/perfis.json`, `data/vcam.json`, `data/vsen.json` | Aba Governo: perfis, propostas e votações. |
| `data/leis/` | Aba Leis. |
| `data/upd/kit.json` | Scripts usados pela atualização diária automática. |
| `scripts/atualizacao/` | Atualização diária de Índices, Governo e Leis. |
| `scripts/mapa/build_mapa.py` | Gera os dados do Mapa a partir das candidaturas do TSE. |
| `scripts/perfis-municipais/` | Gera os perfis de prefeitos, vices e vereadores (votação, histórico, bens e salário). |

## Fontes

Tribunal Superior Eleitoral (candidaturas, resultados e bens declarados), Câmara dos Deputados, Senado Federal, IBGE, Banco Central, Ipea/Ipeadata, Tesouro Nacional, PNUD, Fórum Brasileiro de Segurança Pública, INPE e Tribunal de Contas da Paraíba (folha de pagamento municipal). Cada índice e cada perfil cita a sua fonte na própria página.

CPF e título de eleitor são usados só internamente pelos scripts para ligar candidaturas da mesma pessoa e nunca são gravados nos arquivos de dados.
