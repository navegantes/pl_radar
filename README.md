
<h1 align="center">PL Radar — Painel e Backend de Dados Legislativos</h1> 

<p align="center">
  <img alt="Principal linguagem do projeto" src="https://img.shields.io/github/languages/top/navegantes/pl_radar?color=3B82F6">

  <img alt="Quantidade de linguagens utilizadas" src="https://img.shields.io/github/languages/count/navegantes/pl_radar?color=3B82F6">

  <img alt="Tamanho do repositório" src="https://img.shields.io/github/repo-size/navegantes/pl_radar?color=3B82F6">

  <img alt="Licença" src="https://img.shields.io/github/license/navegantes/pl_radar?color=3B82F6">

  <img alt="Github forks" src="https://img.shields.io/github/forks/navegantes/pl_radar?color=3B82F6" />

  <img alt="Github stars" src="https://img.shields.io/github/stars/navegantes/pl_radar?color=3B82F6" />
</p>

<hr>

<br>

<div align="center" id="top"> 
  <img src="./public/img/home.png" alt="pl_radar home" />
</div>

<hr>


## Sobre

O PL Radar é uma aplicação web destinada ao acompanhamento, consulta e análise de propostas legislativas do Senado Federal brasileiro.

O objetivo é centralizar informações sobre projetos de lei, permitir a pesquisa e o acompanhamento de sua tramitação e apresentar indicadores que ajudem a compreender a atividade legislativa.

A aplicação utiliza dados disponibilizados pela API de Dados Abertos do Senado Federal.

Além da consulta individual de proposições, o projeto prevê uma camada de análise estatística, denominada Panorama Legislativo, com gráficos e indicadores sobre a produção legislativa.

O PL Radar mantém a interface original em HTML, CSS e JavaScript puro e acrescenta um backend FastAPI, uma camada de aplicação e persistência SQLAlchemy. O banco inicial é SQLite. A camada de domínio/aplicação depende de portas (interfaces), não do banco concreto.

## Estrutura

```text
pl_radar/
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── script.js              # Orquestração da interface
│   ├── package.json
│   └── js/
│       └── api-client.js      # Adapter HTTP
├── backend/
│   ├── app/
│   │   ├── api/                 # Rotas HTTP / contratos de entrada e saída
│   │   ├── application/         # Casos de uso, normalização e agregações
│   │   ├── domain/              # Entidades e portas (interfaces)
│   │   └── infrastructure/     # SQLAlchemy, SQLite/PostgreSQL e cliente Senado
│   ├── migrations/              # Migrações Alembic
│   └── tests/
│   └── data/                    # Banco SQLite local (não versionado)
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Princípios aplicados

- **Clean Architecture:** domínio e casos de uso não importam FastAPI, HTTPX ou SQLAlchemy.
- **Dependency Inversion / DI:** `ProposalRepository` e `SenadoGateway` são portas; o módulo de dependências injeta os adaptadores concretos.
- **Repository Pattern:** consultas e persistência ficam em `SqlAlchemyProposalRepository`.
- **Adapter Pattern:** `SenadoApiClient` encapsula a API do Senado no backend; `ApiClient` encapsula o transporte HTTP no frontend.
- **Use Case / Service Layer:** sincronização e agregação estatística são casos de uso independentes das rotas.
- **Single Responsibility:** API, aplicação, domínio e infraestrutura têm responsabilidades distintas.
- **Persistência substituível:** SQLAlchemy abstrai o dialeto. Para PostgreSQL, altere `DATABASE_URL`; não altere casos de uso nem rotas.

## Executar localmente

Requer Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # opcional; ajuste as variáveis conforme necessário
cd backend
uvicorn app.main:app --reload
```

Abra `http://localhost:8000`. A API interativa fica em `http://localhost:8000/docs` e a verificação de saúde em `/api/v1/health`.

O backend tenta uma sincronização inicial quando o banco está vazio. Por padrão, também executa sincronização a cada seis horas. O botão **Atualizar** solicita uma sincronização imediata. A listagem e os gráficos consultam o banco local, não fazem uma chamada externa por carregamento da página.

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `sqlite+pysqlite:///./data/pl_radar.db` | URL SQLAlchemy do banco |
| `SENADO_BASE_URL` | `https://legis.senado.leg.br/dadosabertos` | Raiz dos Dados Abertos |
| `SYNC_ON_STARTUP` | `true` | Sincroniza se o banco estiver vazio |
| `AUTO_CREATE_SCHEMA` | `true` | Cria tabelas automaticamente no startup (desative ao usar Alembic em produção) |
| `SYNC_INTERVAL_SECONDS` | `21600` | Intervalo de sincronização automática; `0` desativa |
| `REQUEST_TIMEOUT_SECONDS` | `45` | Timeout do cliente HTTP |
| `CORS_ORIGINS` | `*` | Origens permitidas quando frontend e backend forem separados |

## PostgreSQL no futuro

Instale o driver já listado em `requirements.txt` e configure, por exemplo:

```env
DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/pl_radar
```

A aplicação cria o engine pelo `DATABASE_URL`. Os repositórios usam SQLAlchemy e tipos portáveis. A migração requer criar o banco PostgreSQL, configurar a variável e executar as migrações. Não é necessário alterar os casos de uso ou o JavaScript.

Para implantação e evolução do schema, use Alembic:

```bash
cd backend
alembic -c alembic.ini upgrade head
```

A criação automática de tabelas no startup é conveniente para desenvolvimento inicial; em produção, execute `alembic upgrade head` e configure `AUTO_CREATE_SCHEMA=false`.

## Endpoints do backend

| Método | Rota | Responsabilidade |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/proposals` | Lista local com filtros opcionais |
| `GET` | `/api/v1/statistics` | Agregações estatísticas locais |
| `POST` | `/api/v1/sync` | Sincronização imediata com o Senado |
| `GET` | `/api/v1/processes/{id}` | Proxy de detalhes do processo |
| `GET` | `/api/v1/senators/{code}/profile` | Proxy do XML de perfil parlamentar |

## Persistência e modelo

Tabelas criadas:

- `proposals`: dados normalizados e JSON original da API.
- `proposal_snapshots`: fotografia do estoque total/em tramitação em cada sincronização.
- `sync_logs`: histórico de execução das sincronizações.
- `parliamentarians`, `authorships`, `party_affiliations`: estrutura preparada para cadastro, autoria e histórico partidário.
- `vote_events`, `votes`: estrutura preparada para eventos e votos individualizados.
- `proceeding_events`, `rapporteurs`: estrutura preparada para tramitação e relatorias.

As tabelas complementares estão preparadas, mas não são preenchidas automaticamente nesta primeira entrega. A coleta de votações exige validar os formatos reais das respostas, identificadores de votação e vínculo com processos antes de habilitar gráficos de ranking. O painel exibe essa indisponibilidade explicitamente, sem inventar valores.

## Estatísticas atualmente alimentadas

- Evolução mensal de proposições apresentadas.
- Distribuição por situação atual.
- Distribuição por tipo de documento.
- Autoria estruturada quando a resposta fornece uma lista de autores.
- Snapshot do total e do total em tramitação por execução.

**Limites conhecidos:** o endpoint de listagem pode fornecer autoria como texto agregado; strings não são divididas artificialmente em nomes para não contar coautores como autores individuais. Assuntos, partidos e UFs dependem de dados estruturados ou enriquecimento por endpoints próprios. O gráfico de proposições mais votadas permanece desabilitado até a coleta nominal ser implementada e validada.

Os snapshots começam a ser registrados a partir da primeira sincronização desta versão; eles não reconstroem retroativamente o estoque histórico.

## Testes

```bash
cd backend
PYTHONPATH=. pytest -q
```

## Interface e funcionalidades preservadas

A identidade neobrutalista, tema claro/escuro, filtros, pesquisa, paginação, tela de detalhes, autoria com dropdown e links oficiais foram mantidos. O cliente HTTP do frontend foi isolado em `frontend/js/api-client.js`, separado da lógica de apresentação. As chamadas diretas do navegador à API do Senado foram substituídas pelo backend, evitando dependência de CORS no navegador.

O painel é informativo: não envia votos, comentários ou manifestações ao Senado.
