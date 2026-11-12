# PL Radar — Painel de monitoramento legislativo

Painel estático em HTML, CSS e JavaScript para acompanhar processos legislativos disponibilizados pela API de Dados Abertos do Senado Federal.

## Estrutura

```text
painel_pl_senado/
├── index.html
├── styles.css
├── script.js
└── README.md
```

## Como executar

A forma recomendada é servir a pasta por HTTP local (não abrir o HTML diretamente como `file://`):

### Python

```bash
cd painel_pl_senado
python -m http.server 8000
```

Acesse `http://localhost:8000`.

Também é possível usar a extensão Live Server do VS Code.

## Fonte de dados

O painel consulta:

`https://legis.senado.leg.br/dadosabertos/processo?v=1`

A resposta esperada é uma lista JSON com campos como `identificacao`, `ementa`, `dataApresentacao`, `autoria`, `situacaoAtual`, `tramitando` e `id`.

A aplicação ordena localmente por `dataApresentacao` (mais recente primeiro), filtra os tipos de proposição e pagina a exibição em lotes de 20 itens.

## Consulta pública

Quando o registro contém `codigoMateria`, o painel monta:

`https://www12.senado.leg.br/ecidadania/visualizacaomateria?id={codigoMateria}`

O campo `codigoMateria` é usado no link do e-Cidadania. O campo `id` é o identificador interno do processo e é usado para consultar os detalhes.

## Tela de detalhes

Cada card possui o botão **Ver detalhes**, que consulta `https://legis.senado.leg.br/dadosabertos/processo/{id}?v=1`. A tela apresenta resumo, ementa, autoria, classificação temática, movimentações, despachos, processos apensados/relacionados e link para o documento oficial, conforme os dados disponíveis na resposta. O botão de retorno mantém o painel e seus filtros em memória.

A tela de detalhes também respeita o tema claro/escuro. A consulta usa o `id` interno do processo; o link do e-Cidadania continua usando `codigoMateria`.

## Observações técnicas

- Atualização automática a cada 5 minutos e botão para atualizar manualmente.
- O filtro inicial mostra tipos de proposição relacionados a projetos de lei (`PL`, `PLS`, `PLC`, `PLP`, `PLV` e registros cujo tipo textual indica projeto de lei).
- O filtro "PL — tipo exato" limita a identificação ao prefixo `PL`.
- Tema claro/escuro com preferência guardada em `localStorage`.
- O painel depende de o navegador conseguir acessar a API diretamente. Se a API não liberar CORS para a origem usada, será necessário um pequeno proxy/backend (por exemplo, FastAPI, Flask ou Cloudflare Worker). O próprio painel mostra um aviso nesse caso.
- A consulta da API sem parâmetros pode retornar um conjunto grande. Para produção, recomenda-se confirmar os parâmetros de filtro e limites/paginação suportados pela versão atual do serviço e, se necessário, implementar cache no backend.
- O painel é informativo e não envia votos, comentários ou manifestações ao Senado.

## Personalização

- URL da API e URL de consulta pública: constantes no início de `script.js`.
- Intervalo de atualização: `REFRESH_INTERVAL`.
- Quantidade por lote: `PAGE_SIZE`.
- Cores, tipografia e espaçamentos: variáveis CSS no início de `styles.css`.


### Perfis dos autores na tela de detalhes

A seção **Autoria** apresenta um dropdown para cada autor. Ao expandi-lo, o painel consulta sob demanda o endpoint `https://legis.senado.leg.br/dadosabertos/senador/{codigoParlamentar}?v=6`, interpreta o XML no navegador e exibe nome parlamentar e completo, partido/UF, sexo, nascimento, naturalidade, telefone, e-mail, endereço, foto oficial e link para o perfil no Senado, conforme os campos disponíveis. As respostas são mantidas em cache durante a sessão para evitar consultas repetidas.

Autores sem `codigoParlamentar` continuam visíveis, mas não recebem consulta de perfil. A API precisa permitir CORS para que a chamada funcione diretamente no navegador; caso contrário, configure um proxy no backend.
