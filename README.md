# Otimização do Vestibular UFRGS

Aplicação full-stack que encontra uma combinação de acertos nas nove provas do
Vestibular UFRGS capaz de atingir uma nota de corte, respeitando as regras de
eliminação e as restrições definidas pelo usuário.

A formulação matemática original está em
[`Formulação_Problema_Vestibular.pdf`](Formula%C3%A7%C3%A3o_Problema_Vestibular.pdf).

## Regras implementadas

O modelo trabalha com uma escolha inteira de 1 a 15 acertos para cada prova:

`BIO`, `FIS`, `QUI`, `MAT`, `HIS`, `LIT`, `PORT_RED`, `LEM` e `GEO`.

Os seguintes critérios eliminatórios são considerados:

- no mínimo um acerto em cada prova objetiva;
- no mínimo 41 acertos no total das nove provas objetivas;
- escore padronizado objetivo estritamente maior que zero;
- nota bruta de Redação maior ou igual a 4,5, em uma escala de 0 a 15;
- atingimento da nota de corte usada como Argumento de Concorrência mínimo.

A pré-classificação prevista no edital depende da classificação real de todos
os candidatos e não pode ser deduzida apenas das notas informadas. Por isso, a
API devolve explicitamente a premissa de que o candidato ja foi
pré-classificado.

### Redação e Português

A nota bruta de Redação é uma variável de decisão discretizada em passos de
`0,1`, dentro dos limites informados pelo usuário e nunca abaixo de `4,5`.
Cada valor possível é convertido em escore padronizado usando a média e o
desvio padrão do ano:

```text
EP_REDACAO = 500 + 100 * (NOTA_REDACAO - MEDIA_REDACAO) / DESVIO_REDACAO
```

Para cada par formado por acertos em Português e nota da Redação, o escore
usado no AC é:

```text
EP_PORT_RED(acertos, redacao) = (EP_PORTUGUES(acertos) + EP_REDACAO(redacao)) / 2
```

O solver possui uma variável binária para cada combinação permitida. Com a
faixa completa de `4,5` a `15,0`, são 15 × 106 = 1.590 combinações. Para cada
uma, `EP_PORT_RED` e `1 / EP_PORT_RED` são calculados previamente. Isso mantém
linear a restrição da média harmônica, sem exigir que o CBC divida por uma
variável contínua.

Português e Redação têm restrições independentes. A função objetivo da prova
também é escolhida explicitamente:

- `none`: nenhum dos componentes é minimizado;
- `portuguese`: minimiza apenas o EP objetivo de Português;
- `essay`: minimiza apenas o EP da Redação;
- `combined`: minimiza o EP conjunto 50/50.

O Argumento de Concorrência é calculado como média harmônica ponderada:

```text
AC = SOMA(peso_i) / SOMA(peso_i / EP_i)
```

## Fluxo da otimização

1. O frontend envia curso, ano, modalidade, língua estrangeira, limites de
   Português e Redação e o objetivo da prova conjunta.
2. O backend consulta em memoria os escores objetivos, a nota de corte e as
   estatísticas da Redação do ano.
3. O backend cria a grade de Redação em passos de `0,1` dentro da faixa válida.
4. Para cada nota da grade e cada quantidade de acertos em Português, calcula
   previamente `EP_REDACAO`, `EP_PORT_RED` e o inverso usado no AC.
5. O solver escolhe exatamente um par Português/Redação, uma quantidade inteira
   de acertos para cada outra prova, pelo menos 41 acertos e o AC mínimo.
6. A resposta inclui os acertos escolhidos, escores, AC obtido, limiar, dados
   da Redacao e o historico de notas de corte.

## Arquitetura

```text
Frontend React
    |
    | POST /optimize
    v
FastAPI
    |-- database.py                  dados JSON carregados em memória
    |-- essay_scores.py              scraping e cálculo da Redação
    |-- optimization.py              modelo PuLP/CBC
    `-- scripts/update_year_data.py  atualização anual validada
            |-- escores objetivos (requests + BeautifulSoup)
            |-- estatísticas da Redação (requests + BeautifulSoup)
            `-- rankings (Selenium + Chrome)
```

Os arquivos JSON sao usados pela API. Os CSVs equivalentes sao mantidos para
auditoria e inspeção manual.

## Dados

Os arquivos ficam em `backend/data/`:

| Arquivo | Conteúdo |
|---|---|
| `escores_padronizados.json/.csv` | EP por ano, prova e quantidade de acertos |
| `redacao_stats.json/.csv` | média, desvio padrão e volume de redações por ano |
| `rankings_completos.json/.csv` | candidatos usados para obter as notas de corte |
| `course_weights.csv` | pesos das provas por curso |
| `course_mapping.json` | nomes históricos normalizados dos cursos |

No início, `database.load_databases()` carrega os JSONs, transforma os escores
em listas ordenadas de 1 a 15 acertos e pré-calcula a menor nota classificada
por ano, curso e modalidade. Assim, uma requisição de otimização não depende de
scraping em tempo real.

## Atualização anual segura

Execute os comandos a partir de `backend/`. Primeiro valide toda a coleta sem
alterar os arquivos:

```bash
python -m src.scripts.update_year_data --year 2026 --dry-run
```

Se a validação terminar com sucesso, publique o novo ano:

```bash
python -m src.scripts.update_year_data --year 2026
```

Se o ano já existir, a atualização é interrompida. Para uma substituição
intencional, use:

```bash
python -m src.scripts.update_year_data --year 2026 --force
```

O procedimento executa estas protecoes:

1. coleta as tres fontes antes de alterar a base;
2. exige todas as provas e exatamente os escores de 1 a 15 acertos;
3. rejeita escores objetivos menores ou iguais a zero;
4. exige ranking não vazio e sem registros de outro ano;
5. exige média e desvio válido da Redação para o ano solicitado;
6. cria uma copia em `data/backups/AAAAmmdd-HHMMSS/`;
7. grava arquivos temporários e usa substituição atômica nos arquivos finais.

Depois da publicação, reinicie o backend para recarregar os JSONs. Confirme os
anos disponíveis em `GET /data/status`.

O comando é deliberadamente acionado uma vez por ano: as páginas de origem
podem mudar e a etapa de `--dry-run` permite detectar essa mudança antes da
publicação. Ele também pode ser chamado por uma rotina de CI agendada, mantendo
as mesmas validações.

## Fontes

- escores objetivos: `https://www.ufrgs.br/vestibular/cv{ano}/histogramas/`;
- rankings: `https://www1.ufrgs.br/PortalEnsino/GraduacaoProcessoSeletivo/index.php/DivulgacaoDadosChamamento`;
- estatísticas da Redação:
  `https://fisica.net/passenaufrgs/estatisticas/medias-da-redacao.php`.

## API

### `GET /health`

Retorna `{"status": "ok"}`.

### `GET /data/status`

Lista os anos carregados separadamente para escores, rankings e Redação. Isso
permite verificar se um ano está completo antes de disponibilizá-lo no
frontend.

### `POST /optimize`

Exemplo de requisição:

```json
{
  "course": "Ciência da Computação - Bacharelado",
  "constraints": {
    "MAT": [[">=", 8], ["<=", 15]]
  },
  "min_subjects": ["MAT"],
  "foreign_language": "Inglês",
  "reference_year": "2025",
  "entry_method": "LI_EP",
  "essay_constraints": {
    "min": 4.5,
    "max": 12.5
  },
  "port_red_objective": "essay"
}
```

Campos:

| Campo | Tipo | Descrição |
|---|---|---|
| `course` | `str` | Nome canônico do curso |
| `constraints` | `dict` | Limites `>=` e `<=` de acertos por prova |
| `min_subjects` | `list[str]` | Provas comuns incluídas na função objetivo; não deve conter `PORT_RED` |
| `foreign_language` | `str` | Língua estrangeira escolhida |
| `reference_year` | `str` | Ano comum aos tres conjuntos de dados |
| `entry_method` | `str` | Modalidade de ingresso |
| `essay_constraints` | `object` | Limites `min` e `max` da Redação, entre 4,5 e 15 |
| `port_red_objective` | `str` | `none`, `portuguese`, `essay` ou `combined` |

Uma resposta normal inclui `chosen_hits`, `AC`, `threshold`, `solve_status`,
`essay`, `port_red_objective`, `assumptions` e `graphJson`. Dentro de
`chosen_hits.PORT_RED` são devolvidos os acertos de Português, o EP de
Português, a nota e o EP da Redação e o EP conjunto.

## Estrutura principal

```text
backend/
|-- data/
|-- src/
|   |-- main.py
|   |-- database.py
|   |-- essay_scores.py
|   |-- optimization.py
|   `-- scripts/
|       |-- save_scores.py
|       |-- save_rankings.py
|       `-- update_year_data.py
`-- tests/

frontend/
`-- src/pages/
    |-- Home/
    `-- Results/
```

## Execução

### Docker

```bash
docker compose up --build
```

- frontend: `http://localhost:3000`;
- backend: `http://localhost:8000`;
- documentação interativa: `http://localhost:8000/docs`.

### Desenvolvimento local

Backend, a partir da raiz do projeto:

```bash
cd backend
python -m venv .venv
python -m pip install -r requirements-dev.txt
uvicorn src.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm start
```

O scraping de rankings usa Selenium e requer Google Chrome. O container do
backend já instala o navegador necessário.

## Testes

A partir de `backend/`:

```bash
python -m pytest
```

Os testes unitários cobrem parsing de escores e rankings, grade decimal da
Redação, composição 50/50, escolha conjunta do solver e validações da atualização
anual. Testes que acessam páginas
reais ou um navegador são marcados como `integration` e ficam desabilitados por
padrão:

```bash
python -m pytest -m integration
```

Para o frontend:

```bash
cd frontend
set CI=true
npm test
```

## Tecnologias

- backend: Python, FastAPI, PuLP/CBC, BeautifulSoup e Selenium;
- frontend: React, React Router e Recharts;
- infraestrutura: Docker, Docker Compose e nginx.
