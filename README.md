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
2. O backend consulta em memória os escores objetivos e as estatísticas da
   Redação, e obtém a nota de corte do último snapshot confirmado no SQLite.
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
    | POST /optimize e GET /rankings/candidates
    v
FastAPI
    |-- database.py                  escores em memória e rankings no SQLite
    |-- essay_scores.py              scraping e cálculo da Redação
    |-- optimization.py              modelo PuLP/CBC
    |-- ranking_repository.py        estado, histórico, locks e backups
    |-- sync_rankings.py             sincronização manual de candidatos
    |-- ranking_scheduler.py         agendamento diário com APScheduler
    `-- update_year_data.py          atualização anual validada
            |-- escores objetivos (requests + BeautifulSoup)
            `-- estatísticas da Redação (requests + BeautifulSoup)
```

Escores objetivos e estatísticas de Redação mudam uma vez por edição e
continuam versionados como JSON/CSV. Rankings são mutáveis e ficam em
`rankings.db`, num volume Docker compartilhado entre API e sincronizador. Cada
consulta abre o SQLite, portanto uma sincronização publicada passa a valer sem
reiniciar a API.

## Dados

Os arquivos ficam em `backend/data/`:

| Arquivo | Conteúdo |
|---|---|
| `escores_padronizados.json/.csv` | EP por ano, prova e quantidade de acertos |
| `redacao_stats.json/.csv` | média, desvio padrão e volume de redações por ano |
| `rankings_completos.json/.csv` | bootstrap legado anônimo, mantido temporariamente |
| `course_weights.csv` | pesos das provas por curso |
| `course_mapping.json` | nomes históricos normalizados dos cursos |

O banco `rankings.db` não é versionado. Ele contém o estado atual dos candidatos,
histórico somente dos campos alterados, execuções por curso, erros, metadados e
o lock de exclusão mútua. A inscrição publicada pela UFRGS serve apenas para
gerar uma chave SHA-256; a inscrição original não é gravada nem exposta.

Na primeira inicialização, o JSON legado é importado uma única vez como
bootstrap anônimo. Um snapshot detalhado de um curso substitui os registros
legados correspondentes. Somente vestibulares de 2022 em diante recebem
backfill de nomes e datas; anos anteriores permanecem apenas para dados
agregados legados.

## Atualização anual segura

Execute os comandos a partir de `backend/`. Primeiro valide toda a coleta sem
alterar os arquivos:

```bash
python -m src.update_year_data --year 2026 --dry-run
```

Se a validação terminar com sucesso, publique o novo ano:

```bash
python -m src.update_year_data --year 2026
```

Se o ano já existir, a atualização é interrompida. Para uma substituição
intencional, use:

```bash
python -m src.update_year_data --year 2026 --force
```

O procedimento executa estas proteções:

1. coleta as duas fontes anuais antes de alterar a base;
2. exige todas as provas e exatamente os escores de 1 a 15 acertos;
3. rejeita escores objetivos menores ou iguais a zero;
4. exige média e desvio válido da Redação para o ano solicitado;
5. cria uma cópia em `data/backups/AAAAmmdd-HHMMSS/`;
6. grava arquivos temporários e usa substituição atômica nos arquivos finais.

Depois da publicação anual, reinicie o backend para recarregar os JSONs de
escores e Redação. Confirme os anos disponíveis em `GET /data/status`.

O comando é deliberadamente acionado uma vez por ano: as páginas de origem
podem mudar e a etapa de `--dry-run` permite detectar essa mudança antes da
publicação.

## Sincronização diária dos rankings

O sincronizador usa uma sessão Selenium por ano, identifica colunas pelo texto
normalizado do cabeçalho e tenta cada curso até três vezes, com espera
progressiva. Uma coluna obrigatória ausente invalida o curso. Cada curso é
validado em staging e publicado em uma transação SQLite independente.

Proteções aplicadas:

1. lock único compartilhado entre execução agendada e manual;
2. backup consistente do SQLite antes da execução, com retenção de 30 dias;
3. rejeição de snapshots vazios, incompletos, duplicados ou menores que 80% do
   último estado, salvo uso explícito de `--force`;
4. preservação do snapshot anterior quando um curso falha;
5. inativação somente após duas coletas completas consecutivas sem o candidato;
6. histórico apenas quando nota, situação, data ou campos de vagas mudam;
7. separação entre `status_date`, que é somente a data publicada pela UFRGS, e
   `collected_at`, que registra o instante da coleta.

Comandos manuais, executados a partir de `backend/`:

```bash
# Anos definidos em RANKING_SYNC_YEARS
python -m src.sync_rankings

# Um ou mais anos específicos
python -m src.sync_rankings --year 2025 --year 2026

# Coleta e valida sem publicar candidatos
python -m src.sync_rankings --year 2025 --dry-run

# Retoma, pulando cursos já concluídos no dia
python -m src.sync_rankings --year 2025 --resume

# Backfill retomável de 2022 até o maior ano configurado
python -m src.sync_rankings --from-year 2022 --resume
```

`--force` ignora somente a proteção de queda de 80% e deve ser usado após
verificação manual da fonte. O lock continua valendo.

No Docker Compose, o serviço `ranking-sync` usa a mesma imagem do backend e o
mesmo volume em `/app/runtime`. A configuração padrão é:

```dotenv
RANKING_SYNC_ENABLED=false
RANKING_SYNC_YEARS=2025
RANKING_SYNC_TIME=05:00
TZ=America/Sao_Paulo
RANKING_DB_PATH=/app/runtime/rankings.db
```

Com a flag desabilitada, o container permanece saudável e não cria novos
agendamentos. Para alterar flag, anos ou horário, recrie o serviço. A ativação
recomendada é feita somente depois de criar o volume, executar um `--dry-run`,
concluir o backfill desde 2022 e comparar os cortes produzidos.

## Fontes

- escores objetivos: `https://www.ufrgs.br/vestibular/cv{ano}/histogramas/`;
- rankings: `https://www1.ufrgs.br/PortalEnsino/GraduacaoProcessoSeletivo/index.php/DivulgacaoDadosChamamento`;
- estatísticas da Redação:
  `https://fisica.net/passenaufrgs/estatisticas/medias-da-redacao.php`.

## API

### `GET /health`

Retorna `{"status": "ok"}`.

### `GET /data/status`

Lista os anos carregados separadamente para escores, rankings e Redação, além
da última execução, último sucesso, cursos processados, falhas, duração
derivável pelos timestamps, anos ativos e data de situação mais recente.

### `GET /rankings/candidates`

Consulta uma janela do ranking confirmado. Parâmetros:

| Campo | Obrigatório | Descrição |
|---|---|---|
| `year` | sim | Ano do vestibular |
| `course` | sim | Curso canônico |
| `entry_mode` | não | Modalidade; omitida retorna o curso inteiro |
| `anchor_score` | não | Centraliza a janela na posição estimada da nota |
| `offset` | não | Início explícito da página; tem precedência sobre a centralização |
| `limit` | não | 25 por padrão, máximo 100 |

A resposta contém `items`, `total`, `offset`, `limit`, `anchor_index`,
`simulated_position` e `last_synced_at`. Candidatos empatados com a simulação
ficam antes dela, produzindo uma estimativa conservadora. A inscrição e a
chave interna nunca são retornadas. A rota envia `X-Robots-Tag: noindex,
nofollow` e `Cache-Control: no-store`.

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
|   |-- save_scores.py
|   |-- save_rankings.py
|   `-- update_year_data.py
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

O scheduler inicia desabilitado. Para ativá-lo, defina
`RANKING_SYNC_ENABLED=true` no ambiente do Compose e recrie o serviço
`ranking-sync`.

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

Os testes unitários cobrem parsing por cabeçalho, grade decimal da Redação,
composição 50/50, escolha conjunta do solver, transações do ranking, histórico,
inativação, lock, agendamento, paginação, empates e validações das atualizações.
Testes que acessam páginas reais ou um navegador são marcados como `integration`
e ficam desabilitados por padrão:

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

## Privacidade e retenção

Os nomes e dados de chamamento são coletados da página pública da UFRGS com a
finalidade de apresentar o ranking e atualizar os cortes. Não existe endpoint
de exportação em massa. O histórico guarda apenas mudanças relevantes; backups
locais expiram após 30 dias. Antes da publicação do sistema, a exibição de nomes
completos e os prazos de retenção devem passar por revisão de privacidade/LGPD.
### E2E (Playwright)

Requer o stack Docker rodando (`docker compose up -d`). A partir de `frontend/`:

```bash
# Primeira vez: baixar binários do browser
npx playwright install chromium

# Roda os testes e2e
npx playwright test

# Com browser visível
npx playwright test --headed

# Relatório HTML após a execução
npx playwright show-report
```

## Licença

Copyright © 2026 Maximus Borges. Todos os direitos reservados.

Esse projeto é proprietário. Nenhuma permissão é concedida para copiar, modificar, redistribuir ou usar este software sem permissão escrita explícita.
Ver [LICENSE](./LICENSE).
