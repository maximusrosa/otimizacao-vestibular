# otimizacao-vestibular

Aplicação full-stack que calcula, para cada uma das nove provas do Vestibular da UFRGS, o **número mínimo de acertos** que um candidato precisa obter para ser aprovado num curso/modalidade, minimizando o esforço total exigido.

## O problema

O objetivo é determinar, para cada prova, o número de acertos que satisfaz simultaneamente vários critérios:

- pelo menos 1 acerto por prova;
- um total mínimo de **41 acertos** (~30% das questões);
- um **Argumento de Concorrência (AC)** acima de um valor de referência (ex.: nota do último classificado na mesma cota no ano anterior);
- restrições adicionais definidas pelo usuário (mínimos/máximos por matéria).

…ao mesmo tempo em que **minimiza a soma dos escores padronizados** das provas selecionadas. Trata-se de um problema de programação linear inteira, resolvido com [PuLP](https://coin-or.github.io/pulp/) (solver CBC).

A formulação matemática completa está em [`Formulação_Problema_Vestibular.pdf`](Formulação_Problema_Vestibular.pdf).

## Arquitetura

```text
Frontend (React + Recharts)  ──POST /optimize──▶  Backend (FastAPI)
                                                     │
                                                     ├─ get_scores   → escores padronizados (scraping requests + BeautifulSoup)
                                                     ├─ get_ranking  → nota de corte / AC mínimo (scraping Selenium + Chrome)
                                                     ├─ optimization → modelo de PL inteira (PuLP/CBC)
                                                     └─ utils        → pesos do curso + dados históricos p/ gráfico
```

O frontend coleta o curso, ano de referência, modalidade de ingresso e restrições por matéria, envia ao endpoint `/optimize` e exibe o número de acertos recomendado por prova, o AC atingido e um gráfico histórico das notas de corte.

## Estrutura de arquivos

```text
otimizacao-vestibular/
├── README.md
├── Formulação_Problema_Vestibular.pdf   # Formulação matemática do problema
├── docker-compose.yml                   # Sobe backend + frontend
├── docker-compose.test.yml              # Roda a suíte de testes (incl. integração)
├── pytest.ini                           # Config do pytest (testpaths, markers)
│
├── backend/
│   ├── Dockerfile                       # Multi-stage; instala Chrome p/ Selenium
│   ├── .dockerignore
│   ├── requirements.txt                 # Dependências de runtime
│   ├── requirements-dev.txt             # + pytest, responses
│   ├── data/
│   │   ├── course_weights.csv           # Pesos das provas por curso
│   │   └── course_mapping.json          # Mapeamento de nomes históricos → nome canônico (gerado)
│   ├── src/
│   │   ├── main.py                      # App FastAPI + endpoints (/health, /optimize)
│   │   ├── optimization.py              # Modelo de PL inteira (PuLP)
│   │   ├── get_scores.py                # Scraping dos escores padronizados (requests/BS4)
│   │   ├── get_ranking.py               # Scraping do ranking / AC mínimo (Selenium)
│   │   ├── constants.py                 # Constantes (matérias, URLs, modalidades, ...)
│   │   └── scripts/
│   │       ├── course_names_mapping.py  # ETL: scrape nomes → gera course_mapping.json
│   │       └── utils.py                 # Leitura de pesos + dados do gráfico histórico
│   └── tests/
│       ├── conftest.py
│       ├── fixtures/                    # HTML de exemplo p/ testes de scraping
│       │   ├── histogramas_2025.html
│       │   └── ranking_sample.html
│       ├── test_get_scores.py
│       ├── test_get_ranking.py
│       └── test_integration.py          # Marcado como `integration` (site/browser real)
│
└── frontend/
    ├── Dockerfile                       # Build React + serve via nginx
    ├── .dockerignore
    ├── package.json
    ├── public/
    └── src/
        ├── App.js                       # Rotas (/ e /resultados)
        ├── index.js / index.css
        ├── constants.js                 # Matérias, MIN_HITS, MAX_HITS
        └── pages/
            ├── Home/                    # Formulário de entrada
            │   ├── index.js
            │   ├── view.jsx
            │   └── styles.css
            └── Results/                 # Resultados + gráfico histórico
                ├── index.js
                ├── view.jsx
                └── styles.css
```

## Tecnologias

**Backend:** Python 3.11 · FastAPI · PuLP (CBC) · Selenium + BeautifulSoup4 · Uvicorn
**Frontend:** React 19 · React Router 7 · Recharts
**Infra:** Docker · docker-compose · nginx (serve o build do frontend)

## Como executar

### Com Docker (recomendado)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend (API): http://localhost:8000 — docs interativas em http://localhost:8000/docs

O frontend só sobe depois que o healthcheck do backend (`GET /health`) passa.

### Localmente (desenvolvimento)

**Backend** (a partir de `backend/`, onde `src` é o pacote de topo):

```bash
cd backend
python -m venv backend/.venv && source backend/.venv/bin/activate
pip install -r requirements-dev.txt
uvicorn src.main:app --reload --port 8000
```

> Selenium requer o Google Chrome instalado (o `get_ranking` roda em modo headless).

**Frontend:**

```bash
cd frontend
npm install
npm start          # http://localhost:3000
```

## Testes

Os testes unitários (scraping com fixtures HTML) rodam por padrão; os de integração (que acessam o site da UFRGS / abrem um browser real) são marcados com `integration` e desativados por padrão.

```bash
# Unitários (default — exclui integração)
PYTHONPATH=. pytest

# Somente integração
PYTHONPATH=. pytest -m integration

# Integração dentro de container (traz o Chrome pronto)
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### Rodando os módulos isoladamente

```bash
python -m src.get_scores

python -m src.get_ranking 
```

## API

### `GET /health`
Healthcheck. Retorna `{"status": "ok"}`.

### `POST /optimize`
Recebe curso, restrições, matérias a minimizar, ano de referência e modalidade; retorna o número de acertos recomendado por prova, o AC atingido e os dados do gráfico histórico.

**Request (`UserData`):**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `course` | `str` | Nome do curso (deve casar com `course_weights.csv`) |
| `constraints` | `dict[str, list[[op, valor]]]` | Restrições por matéria (`">="` / `"<="`) |
| `min_subjects` | `list[str]` | Matérias cujo escore será minimizado |
| `reference_year` | `str` | Ano de referência para escores/ranking |
| `entry_method` | `str` | Modalidade de ingresso (ver `ENTRY_MODES`) |
| `std_scores` | `dict[str, list[float]]` | Escores padronizados por matéria |

**Response (`ReturnedData`):** `result` (acertos escolhidos, AC, limiar, status do solver) + `graphJson` (`{ano: nota_de_corte}`).

## Domínio (constantes)

- **Provas** (`SUBJECTS`): `BIO, FIS, QUI, MAT, HIS, LIT, PORT_RED, LEM, GEO`
- **Acertos por prova:** `MIN_HITS = 1` … `MAX_HITS = 15`
- **Modalidades de ingresso** (`ENTRY_MODES`): `AC, LI_EP, LI_PPI, LB_EP, LB_PPI, LI_PCD, LB_PCD, LI_Q, LB_Q`
- **Línguas estrangeiras:** Inglês, Espanhol, Italiano, Francês, Alemão

## Fontes de dados (UFRGS)

- **Escores padronizados:** `https://www.ufrgs.br/vestibular/cv{ano}/histogramas/`
- **Ranking / chamamento:** `https://www1.ufrgs.br/PortalEnsino/GraduacaoProcessoSeletivo/index.php/DivulgacaoDadosChamamento`

</content>
</invoke>
