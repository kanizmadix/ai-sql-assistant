# AI SQL Assistant

Type a question in plain English → Claude generates the SQL → executes against a real SQLite e-commerce database → results appear instantly. Schema is **prompt-cached** for cheap repeated queries.

## Features
- Natural language → SQL via Claude claude-sonnet-4-6
- Schema prompt-cached in user message block (~90% cheaper on repeated queries)
- SELECT-only safety whitelist (blocks DROP, DELETE, INSERT, UPDATE, etc.)
- Pre-seeded e-commerce SQLite DB (customers, products, orders, order_items)
- 10 built-in example questions
- Dark SQL IDE UI with results table

## Project Structure
```
ai-sql-assistant/
├── main.py           # FastAPI — /query, /schema, /examples
├── sql_generator.py  # NL→SQL via Claude, schema prompt-cached
├── db.py             # SQLite connection + safe query executor
├── sample_data.py    # Seeds ecommerce.db with realistic data
├── ecommerce.db      # Pre-built database (committed, ready to use)
├── requirements.txt
└── templates/
    └── index.html    # Dark SQL IDE UI with example chips
```

## Setup & Run
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload --port 8000
# Open http://localhost:8000
# ecommerce.db is already seeded — no extra setup needed
```

## API
| Method | Endpoint | Body | Returns |
|--------|----------|------|---------|
| GET | `/` | — | HTML UI |
| POST | `/query` | `{question: string}` | `{sql, columns, results, error, row_count}` |
| GET | `/schema` | — | `{schema: string}` |
| GET | `/examples` | — | `{examples: [string]}` |

## Example Questions
- "Show me the top 5 customers by total spending"
- "Which products are low on stock (less than 50 units)?"
- "What is the total revenue by product category?"
- "List all orders placed in 2024 with customer names"

## Database Schema
```
customers    (id, name, email, city, created_at)
products     (id, name, category, price, stock_quantity)
orders       (id, customer_id, order_date, status, total_amount)
order_items  (id, order_id, product_id, quantity, unit_price)
```

## Tech Stack
- **Backend:** FastAPI + Python 3.11+
- **Database:** SQLite (stdlib sqlite3, no driver needed)
- **AI:** Anthropic Claude claude-sonnet-4-6 with prompt caching
- **Frontend:** Vanilla HTML/CSS/JS (dark SQL IDE theme)
