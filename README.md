# AI SQL Assistant

Enterprise-grade natural-language to SQL workbench. Ask in plain English, get
SQL, results, charts, optimization advice, and follow-up questions — backed by
Anthropic Claude with prompt caching.

## Highlights

- **NL → SQL** via Claude `claude-sonnet-4-6` with `cache_control` ephemeral
  caching of the schema (≈90% cheaper on repeat queries).
- **SELECT-only safety guard** rejects DDL/DML before execution.
- **Multi-database registry** — register multiple SQLite files by short name.
- **Schema explorer** with row counts, PK/FK/index introspection and a
  Mermaid ER diagram.
- **Query history** (auto-logged) and **saved queries** in an isolated
  metadata SQLite database.
- **Explain & Optimize** — Claude turns SQL into plain English or suggests
  faster rewrites.
- **Auto chart suggestion** (bar / line / pie / scatter / table) with
  Chart.js-ready payloads.
- **Exports**: CSV, JSON, Markdown table, Excel (`.xlsx`).
- **Follow-up question generator** powered by Claude.
- **In-memory token-bucket rate limiter** middleware.
- **Structured JSON logging** for production observability.
- **Pydantic v2 settings** with `.env` support.
- **Dark SQL IDE UI** with DB picker, ERD, history sidebar, saved queries,
  Explain/Optimize buttons, chart preview, export dropdown, and follow-up chips.
- **Tests** (pytest), **Linting** (ruff), **CI** (GitHub Actions),
  **Docker + docker-compose**, **Makefile**.

## Project Structure

```
ai-sql-assistant/
├── main.py                # FastAPI app — see "API" below
├── config.py              # pydantic-settings configuration
├── logger.py              # structured JSON logging
├── models.py              # Pydantic v2 request/response models
├── prompts.py             # centralized Claude system prompts
├── sql_generator.py       # NL→SQL via Claude, schema prompt-cached
├── query_explainer.py     # Claude-backed SQL→English explainer
├── query_optimizer.py     # Claude-backed optimizer (suggestions + rewrite)
├── query_validator.py     # local pre-validation
├── schema_analyzer.py     # PK/FK/index/row-count introspection
├── schema_visualizer.py   # Mermaid ER diagram generator
├── charts.py              # heuristic chart-type suggester
├── exporter.py            # CSV / JSON / Markdown / Excel
├── followup.py            # Claude-backed follow-up questions
├── history.py             # metadata DB: history + saved queries + tags
├── db.py                  # primary SELECT-only executor
├── db_registry.py         # multi-DB registry
├── exceptions.py          # domain exceptions + FastAPI handlers
├── rate_limiter.py        # token-bucket middleware
├── sample_data.py         # seeds ecommerce.db with 8 tables
├── ecommerce.db           # pre-seeded SQLite database
├── tests/                 # pytest suite
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml         # ruff + pytest config
├── Makefile
├── .env.example
├── requirements.txt
└── templates/index.html   # dark SQL IDE UI
```

## Quickstart

```bash
git clone https://github.com/kanizmadix/ai-sql-assistant.git
cd ai-sql-assistant
cp .env.example .env          # then fill in ANTHROPIC_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python sample_data.py          # (re)seed ecommerce.db
uvicorn main:app --reload --port 8000
# Open http://localhost:8000
```

Or with Docker:

```bash
make docker-build
ANTHROPIC_API_KEY=sk-ant-... make docker-run
```

## API

| Method | Endpoint                       | Description                                  |
|--------|--------------------------------|----------------------------------------------|
| GET    | `/`                            | Dark SQL IDE                                 |
| GET    | `/health`                      | Health check                                 |
| POST   | `/query`                       | NL→SQL, execute, log to history              |
| GET    | `/databases`                   | List registered databases                    |
| GET    | `/schema`                      | Default DB schema (string)                   |
| GET    | `/schema/{db_name}`            | Schema for a specific DB                     |
| GET    | `/schema/{db_name}/analyze`    | Structured `SchemaSummary`                   |
| GET    | `/schema/{db_name}/erd`        | Mermaid ER diagram                           |
| POST   | `/explain`                     | Plain-English explanation of a SQL query     |
| POST   | `/optimize`                    | Optimization suggestions + optional rewrite  |
| POST   | `/chart-suggest`               | Chart.js config for given columns/rows       |
| POST   | `/export/{format}`             | csv / json / markdown / excel                |
| GET    | `/history?limit=&offset=`      | Paginated query history                      |
| GET    | `/history/search?q=`           | Search history                               |
| GET    | `/history/{id}`                | Get a single history record                  |
| DELETE | `/history/{id}`                | Delete a history record                      |
| GET    | `/saved`                       | List saved queries                           |
| POST   | `/saved`                       | Create/update a saved query                  |
| GET    | `/saved/{id}`                  | Get a saved query                            |
| DELETE | `/saved/{id}`                  | Delete a saved query                         |
| POST   | `/followup`                    | Suggested follow-up NL questions             |
| GET    | `/examples`                    | Built-in example questions                   |

## Database Schema (ecommerce.db)

8 tables, several thousand rows of realistic seed data:

| Table       | Approximate size |
|-------------|-----------------:|
| customers   | 200              |
| categories  | 10               |
| suppliers   | 15               |
| employees   | 25               |
| products    | 31               |
| addresses   | 300              |
| orders      | 1500             |
| reviews     | 600              |

## Development

```bash
make install     # pip install -r requirements.txt
make seed        # python sample_data.py
make dev         # uvicorn --reload
make test        # pytest -q
make lint        # ruff check
make format      # ruff format
```

## Configuration

Environment variables (see `.env.example`):

| Variable                   | Default              |
|----------------------------|----------------------|
| `ANTHROPIC_API_KEY`        | (required)           |
| `MODEL`                    | `claude-sonnet-4-6`  |
| `LOG_LEVEL`                | `INFO`               |
| `DATA_DB_PATH`             | `./ecommerce.db`     |
| `META_DB_PATH`             | `./metadata.db`      |
| `RATE_LIMIT_CAPACITY`      | `60`                 |
| `RATE_LIMIT_REFILL_PER_SEC`| `1.0`                |

## Tech Stack

- **Backend:** FastAPI + Python 3.11+
- **Database:** SQLite (stdlib `sqlite3`)
- **AI:** Anthropic Claude `claude-sonnet-4-6` with prompt caching
- **Frontend:** Vanilla HTML/CSS/JS, Mermaid.js (ERD), Chart.js (charts)
- **Quality:** pytest, ruff, GitHub Actions CI, Docker

## License

MIT.
