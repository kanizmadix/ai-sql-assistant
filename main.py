"""
FastAPI backend for the AI SQL Assistant.

Endpoints:
  POST /query    — translate natural language to SQL and execute it
  GET  /schema   — return the current database schema
  GET  /examples — return example questions
"""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from db import get_schema, execute_query
from sql_generator import generate_sql

app = FastAPI(title="AI SQL Assistant", version="1.0.0")

_HTML = Path(__file__).parent / "templates" / "index.html"

# ── Cache the schema once at startup (it doesn't change at runtime) ─────────
_cached_schema: str | None = None


def _get_schema() -> str:
    global _cached_schema
    if _cached_schema is None:
        _cached_schema = get_schema()
    return _cached_schema


# ── Request / response models ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    sql: str
    columns: list[str]
    results: list[list]
    error: str | None = None
    row_count: int = 0


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=_HTML.read_text(encoding="utf-8"))


@app.post("/query", response_model=QueryResponse)
async def query(body: QueryRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    schema = _get_schema()

    # Step 1: translate NL → SQL via Claude (schema is cached after first call)
    try:
        sql = generate_sql(question, schema)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Claude API error: {exc}",
        )

    # Step 2: execute the generated SQL safely
    result = execute_query(sql)

    return QueryResponse(
        sql=sql,
        columns=result["columns"],
        results=result["results"],
        error=result.get("error"),
        row_count=len(result["results"]),
    )


@app.get("/schema")
async def schema():
    return {"schema": _get_schema()}


@app.get("/examples")
async def examples():
    return {
        "examples": [
            "Show me the top 5 customers by total spending",
            "Which products are low on stock (less than 50 units)?",
            "What is the total revenue by product category?",
            "List all orders placed in 2024 with customer names",
            "What are the most popular products by number of orders?",
            "Show customers from New York who have placed at least one order",
            "What is the average order value per customer?",
            "Which customers have never placed an order?",
            "Show monthly revenue for the last 12 months",
            "List the top 3 selling products in the Electronics category",
        ]
    }
