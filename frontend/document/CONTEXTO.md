# PL Radar — Contexto do Projeto

> Documento de contexto técnico e histórico para continuidade do desenvolvimento com modelos de linguagem (LLMs).
>
> **Última atualização:** 08/11/2026  
> **Projeto:** PL Radar  
> **Idioma principal:** Português brasileiro

---

## 1. Visão geral

O PL Radar é uma aplicação web destinada ao acompanhamento, consulta e análise de propostas legislativas do Senado Federal brasileiro.

O objetivo é centralizar informações sobre projetos de lei, permitir a pesquisa e o acompanhamento de sua tramitação e apresentar indicadores que ajudem a compreender a atividade legislativa.

A aplicação utiliza dados disponibilizados pela API de Dados Abertos do Senado Federal.

Além da consulta individual de proposições, o projeto prevê uma camada de análise estatística, denominada **Panorama Legislativo**, com gráficos e indicadores sobre a produção legislativa.

A interface deve manter uma identidade visual própria, baseada em neobrutalismo, com aparência moderna, organizada e profissional.

## 2. Histórico do desenvolvimento

### 2.1. Primeira versão da interface

O desenvolvimento começou com uma aplicação web utilizando:

- HTML;
- CSS;
- JavaScript puro;
- API de Dados Abertos do Senado Federal.

A primeira interface foi organizada em torno de:

- Cabeçalho e identidade visual PL Radar;
- Apresentação principal (hero);
- Indicadores estatísticos;
- Campo de pesquisa;
- Filtros;
- Listagem de projetos de lei;
- Paginação.

Foi escolhida uma identidade visual neobrutalista, com:

- Fundo bege;
- Bordas pretas grossas;
- Sombras duras;
- Amarelo, rosa e azul pastel;
- Tipografia Space Grotesk e DM Mono;
- Alternância entre tema claro e escuro.

A decisão foi preservar a primeira proposta visual como base do produto.

### 2.2. Integração com a API do Senado

A principal fonte de dados é:

`https://legis.senado.leg.br/dadosabertos/processo?v=1`

A consulta pública de uma matéria utiliza o identificador `codigoMateria`:

`https://www12.senado.leg.br/ecidadania/visualizacaomateria?id={codigoMateria}`

É importante distinguir dois identificadores presentes nos dados:

- `id`: identificador interno do processo, utilizado para consultar detalhes.
- `codigoMateria`: identificador utilizado na URL pública do e-Cidadania.

Exemplo:

- `id`: 9123126
- `codigoMateria`: 176233
- Identificação: PL 5789/2026

O endpoint de detalhes é:

`https://legis.senado.leg.br/dadosabertos/processo/{id}?v=1`

Para consultar o perfil de um parlamentar:

`https://legis.senado.leg.br/dadosabertos/senador/{codigoParlamentar}?v=6`

O endpoint de perfil retorna XML.

### 2.3. Funcionalidades implementadas antes da reorganização arquitetural

A interface passou a contar com:

**Consulta de proposições**
- Listagem de projetos;
- Pesquisa;
- Filtros;
- Paginação.

**Detalhes da proposição**
- Identificação;
- Situação;
- Resumo;
- Ementa;
- Autoria;
- Classificação temática;
- Tramitação;
- Despachos;
- Processos apensados;
- Documentos;
- Link para consulta no e-Cidadania.

A navegação de detalhes utiliza histórico do navegador e hash no formato:

`#detalhes/{id}`

**Informações dos parlamentares**
- Dropdown de autores;
- Consulta sob demanda;
- Cache das respostas;
- Foto;
- Nome;
- Partido e UF;
- Informações biográficas;
- Telefone e e-mail;
- Endereço parlamentar;
- Link para perfil oficial.

### 2.4. Evolução para uma arquitetura com backend

Foi identificada a necessidade de reorganizar o projeto para:

- Evitar chamadas diretas do navegador à API externa;
- Reduzir problemas relacionados a CORS;
- Centralizar a integração com o Senado;
- Persistir dados localmente;
- Permitir estatísticas históricas;
- Facilitar a manutenção;
- Possibilitar futura migração de banco de dados.

Foi implementada uma arquitetura com frontend e backend separados.

### 2.5. Implementação da seção Panorama Legislativo

Foi planejada e adicionada à interface uma seção de estatísticas chamada **Panorama Legislativo**.

Ela contempla:

- Evolução mensal das proposições;
- Distribuição por situação;
- Distribuição por tipo de proposição;
- Informações sobre autoria;
- Painel de votações nominais.

O painel de votações nominais deve informar claramente quando ainda não existem dados disponíveis. Não devem ser apresentados números fictícios.

A coleta estruturada de votações ainda precisa ser implementada e validada.

## 3. Arquitetura atual

### 3.1. Visão geral

A aplicação utiliza:

- Frontend: HTML, CSS e JavaScript;
- Backend: Python e FastAPI;
- Banco de dados: SQLite;
- ORM: SQLAlchemy 2.x;
- Migrações: Alembic;
- Integração externa: API de Dados Abertos do Senado.

O backend atua como intermediário entre a interface, o banco de dados e a API externa.

O navegador não deve consultar diretamente a API do Senado.

### 3.2. Estrutura de diretórios

Estrutura implementada:

```text
pl_radar_work/
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── script.js
│   ├── package.json
│   └── js/
│       └── api-client.js
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── main.py
│   │
│   ├── migrations/
│   ├── tests/
│   └── alembic.ini
│
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### 3.3. Clean Architecture

O backend foi organizado em camadas:

**API**
- Define endpoints;
- Recebe requisições;
- Valida parâmetros;
- Encaminha operações para a camada de aplicação.

**Application**
- Implementa casos de uso;
- Orquestra operações;
- Coordena sincronização;
- Calcula estatísticas.

**Domain**
- Contém regras e conceitos centrais do domínio;
- Define interfaces e contratos;
- Não deve depender de FastAPI, SQLAlchemy ou HTTPX.

**Infrastructure**
- Implementa persistência;
- Implementa comunicação com a API do Senado;
- Contém adaptadores concretos;
- Gerencia detalhes tecnológicos externos.

### 3.4. Princípios e padrões utilizados

A arquitetura aplica:

- Clean Architecture;
- SOLID;
- Dependency Inversion;
- Dependency Injection;
- Repository Pattern;
- Adapter Pattern;
- Use Case Pattern;
- Separação de responsabilidades.

Interfaces como `ProposalRepository` e `SenadoGateway` permitem substituir implementações concretas sem alterar as regras de negócio.

O objetivo é manter o domínio independente dos detalhes de infraestrutura.

### 3.5. Banco de dados

O banco inicial é SQLite, com SQLAlchemy 2.x.

A conexão é configurada por variável de ambiente:

`DATABASE_URL`

A arquitetura permite futura utilização de PostgreSQL, por exemplo:

```env
DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/pl_radar
```

A mudança de banco deve exigir apenas ajustes de configuração e infraestrutura, sem reescrever as regras de negócio ou os contratos das rotas.

Tabelas previstas e implementadas no modelo de persistência:

| Tabela | Responsabilidade |
|---|---|
| `proposals` | Dados principais das proposições |
| `proposal_snapshots` | Histórico de alterações |
| `sync_logs` | Registro de sincronizações |
| `parliamentarians` | Cadastro de parlamentares |
| `authorships` | Relação entre autores e proposições |
| `party_affiliations` | Histórico de filiações partidárias |
| `vote_events` | Eventos de votação |
| `votes` | Votos individuais |
| `proceeding_events` | Eventos de tramitação |
| `rapporteurs` | Relatorias |

**Atenção:** a existência dessas tabelas não significa que todos os dados já estejam sendo coletados. A ingestão estruturada de parlamentares, votações, tramitação e relatorias ainda precisa ser ampliada e validada.

### 3.6. Sincronização

O backend possui:

- Sincronização manual;
- Sincronização automática;
- Registro de sincronizações;
- Persistência local;
- Consulta dos dados armazenados.

A sincronização automática está configurada para ocorrer a cada seis horas.

Quando habilitado, o backend também pode tentar sincronizar dados na inicialização, caso o banco esteja vazio.

A configuração é controlada por variáveis de ambiente.

## 4. Endpoints internos

Rotas implementadas:

| Método | Endpoint | Finalidade |
|---|---|---|
| GET | `/api/v1/health` | Verificar disponibilidade |
| GET | `/api/v1/proposals` | Consultar proposições |
| GET | `/api/v1/statistics` | Consultar estatísticas |
| POST | `/api/v1/sync` | Iniciar sincronização |
| GET | `/api/v1/processes/{id}` | Consultar detalhes de um processo |
| GET | `/api/v1/senators/{code}/profile` | Consultar perfil parlamentar |

O frontend utiliza `frontend/js/api-client.js` para centralizar as chamadas HTTP.

Métodos disponíveis no cliente:

- `listProposals`;
- `synchronize`;
- `getStatistics`;
- `getProcess`;
- `getSenatorProfile`.

## 5. Estado atual da interface

A identidade visual deve permanecer coerente com a primeira versão do PL Radar e com o mockup de referência.

### 5.1. Elementos visuais

- Fundo bege;
- Bordas pretas grossas;
- Sombras duras;
- Amarelo pastel;
- Rosa pastel;
- Azul pastel;
- Tipografia Space Grotesk;
- Tipografia DM Mono;
- Tema claro e escuro;
- Componentes com aparência neobrutalista.

Não substituir essa identidade por uma interface genérica de dashboard corporativo.

### 5.2. Organização do dashboard

A interface deve apresentar:

1. Cabeçalho PL Radar;
2. Alternância de tema;
3. Navegação;
4. Hero com o título Panorama Legislativo;
5. Cards de indicadores;
6. Gráficos estatísticos;
7. Painel de votações nominais;
8. Listagem de projetos de lei.

### 5.3. Gráficos previstos no Panorama Legislativo

**Evolução mensal das proposições**

Gráfico temporal que apresenta a quantidade de proposições por mês.

**Distribuição por situação**

Gráfico de distribuição das matérias conforme sua situação legislativa.

**Tipos de proposição**

Gráfico comparativo de categorias como PL, PLP, PEC, requerimentos e outros tipos, conforme os dados disponíveis.

**Autoria**

Ranking de autores com base nas relações estruturadas entre parlamentares e proposições.

**Votações nominais**

Painel reservado à análise de votações nominais, incluindo quantidade de votos e informações relacionadas às proposições.

Enquanto a coleta não estiver disponível, deve ser exibida uma mensagem informativa, sem simular resultados.

## 6. Mockup de referência e próxima implementação

Foi gerada uma imagem de referência visual para a evolução do dashboard, com o título Panorama Legislativo.

A próxima implementação solicitada é reproduzir essa referência como uma página única HTML pura.

Requisitos:

- Um único arquivo HTML;
- CSS incorporado;
- JavaScript incorporado;
- Sem React, Vue, Angular ou outros frameworks;
- Preservar o layout e a composição visual da imagem;
- Reproduzir os gráficos com recursos implementáveis no navegador;
- Incluir alternância entre tema claro e escuro;
- Manter os textos em português;
- Utilizar dados claramente identificados como demonstrativos quando não forem provenientes da API;
- Não confundir o mockup estático com a aplicação integrada ao backend.

O mockup deve servir como referência visual e protótipo independente. A aplicação principal continua sendo a estrutura `frontend/` e `backend/`.

## 7. Infraestrutura e execução

### Execução local

Na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
cd backend
uvicorn app.main:app --reload
```

Acessos:

- Aplicação: `http://localhost:8000`
- Documentação da API: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

### Migrações

Para aplicar migrações:

```bash
cd backend
alembic -c alembic.ini upgrade head
```

Em produção, utilizar `AUTO_CREATE_SCHEMA=false` após executar as migrações.

O projeto também possui Dockerfile e docker-compose.

## 8. Testes e validações realizadas

Na implementação arquitetural foram executadas as seguintes verificações:

- Testes de normalização;
- Testes de estatísticas;
- Testes de repositório;
- Verificação sintática do JavaScript;
- Compilação dos módulos Python;
- Testes de endpoints com FastAPI TestClient;
- Testes de inicialização e resposta do frontend;
- Aplicação de migração Alembic em banco SQLite temporário.

Resultado registrado:

- 4 testes automatizados passaram;
- `node --check` passou para os arquivos JavaScript;
- `python -m compileall` passou;
- Smoke tests dos endpoints passaram;
- Migração SQLite foi validada.

### Limitação da validação externa

Durante a implementação, o ambiente de desenvolvimento não conseguiu resolver o DNS do domínio externo do Senado.

Por isso, a integração real de sincronização com a API externa não foi validada naquela execução.

É necessário testar em um ambiente com acesso à internet e confirmar os formatos reais das respostas.

Caso necessário, ajustar a normalização dos dados conforme os payloads efetivamente retornados pela API.

Não considerar a sincronização externa validada até que esse teste seja realizado.

## 9. Pendências técnicas

Prioridades para continuidade:

### Prioridade alta

1. Validar a integração real com a API do Senado.
2. Conferir a normalização dos dados recebidos.
3. Validar os vínculos entre processos, matérias e parlamentares.
4. Implementar ingestão estruturada de autoria.
5. Implementar coleta e armazenamento de votações nominais.
6. Implementar os indicadores de votação com dados reais.

### Prioridade intermediária

7. Ampliar a coleta de eventos de tramitação.
8. Implementar histórico confiável de alterações das proposições.
9. Estruturar dados de relatorias.
10. Melhorar a cobertura de testes de integração.
11. Avaliar estratégias de atualização incremental.

### Prioridade futura

12. Migrar para PostgreSQL quando houver necessidade.
13. Implementar autenticação e controle de acesso caso o produto passe a oferecer funcionalidades administrativas.
14. Avaliar cache e otimização para grandes volumes de dados.
15. Evoluir as análises estatísticas e os filtros.

## 10. Regras para continuidade por outros LLMs

Ao continuar o desenvolvimento, seguir obrigatoriamente estas orientações:

1. Preservar a identidade visual neobrutalista do PL Radar.
2. Não substituir a arquitetura existente sem justificativa técnica.
3. Respeitar a separação entre domínio, aplicação, API e infraestrutura.
4. Não introduzir dependências de infraestrutura nas regras de domínio.
5. Utilizar interfaces e injeção de dependência para desacoplar implementações.
6. Preservar a possibilidade de migração SQLite → PostgreSQL.
7. Não remover funcionalidades existentes durante refatorações.
8. Não inventar dados legislativos, votos, autores ou estatísticas.
9. Diferenciar claramente dados reais, dados demonstrativos e dados indisponíveis.
10. Validar os formatos reais da API antes de implementar novos coletores.
11. Atualizar a documentação sempre que houver mudanças arquiteturais relevantes.
12. Executar os testes existentes após alterações.
13. Não afirmar que uma integração foi validada sem executar um teste real.
14. Manter o idioma da interface em português brasileiro.

### Regra fundamental

O PL Radar deve ser tratado como um produto em evolução, não como um projeto novo a cada sessão.

Antes de propor alterações, verificar a estrutura e o código existentes. Reutilizar componentes e funcionalidades já implementados e preservar decisões arquiteturais anteriores, salvo quando houver uma justificativa técnica clara para modificá-las.

---

## 11. Referências técnicas

**API de Dados Abertos do Senado**

`https://legis.senado.leg.br/dadosabertos/processo?v=1`

**Documentação OpenAPI**

`https://legis.senado.leg.br/dadosabertos/v3/api-docs`

**Consulta de matéria no e-Cidadania**

`https://www12.senado.leg.br/ecidadania/visualizacaomateria?id=`

**Tecnologias principais**

- Python;
- FastAPI;
- SQLAlchemy 2.x;
- Alembic;
- SQLite;
- PostgreSQL (migração futura);
- HTML;
- CSS;
- JavaScript.

**Princípios arquiteturais**

- Clean Architecture;
- SOLID;
- Dependency Injection;
- Repository Pattern;
- Adapter Pattern;
- Separation of Concerns.

---

*Fim do documento de contexto do PL Radar.*