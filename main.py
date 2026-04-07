"""
FastAPI backend for the AI SQL Assistant — enterprise edition.

Existing endpoints (still work):
    POST /query, GET /schema, GET /examples

New endpoints include multi-DB support, history & saved queries, schema
explorer with Mermaid ERD, query explanation/optimization, chart suggestions,
exports (CSV/JSON/MD/Excel), and follow-up question generation.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from config import settings
from db import execute_query as execute_local_query
from db_registry import (
    get_connection as registry_conn,
    get_schema as registry_get_schema,
    list_databases as registry_list,
)
import exceptions as exc_mod
from exceptions import (
    DatabaseNotFound,
    QueryFailed,
    UnsafeQuery,
    install_handlers,
)
import history
from charts import suggest_chart
from exporter import CONTENT_TYPES, EXTENSIONS, export
from followup import suggest_followup_questions
from logger import get_logger
from models import (
    ChartConfig,
    ExportRequest,
    NLFollowUp,
    OptimizationSuggestion,
    QueryExplanation,
    QueryHistoryRecord,
    QueryRequest,
    QueryResponse,
    SavedQuery,
    SchemaSummary,
)
from query_explainer import explain_query as ai_explain_query
from query_optimizer import optimize_query as ai_optimize_query
from query_validator import validate_sql
from rate_limiter import TokenBucketRateLimiter
from schema_analyzer import analyze_schema
from schema_visualizer import generate_mermaid_erd
from sql_generator import generate_sql

log = get_logger("sql-assistant")

app = FastAPI(title="AI SQL Assistant", version="2.0.0")

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TokenBucketRateLimiter)
install_handlers(app)


@app.middleware("http")
async def _request_logger(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    dur = (time.perf_counter() - start) * 1000
    log.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(dur, 2),
        },
    )
    return response


# ── Static / template ──────────────────────────────────────────────────────
_HTML_PATH = Path(__file__).parent / "templates" / "index.html"


# ── Schema cache (per DB) ──────────────────────────────────────────────────
_schema_cache: dict[str, str] = {}


def _schema_for(db_name: str) -> str:
    if db_name not in _schema_cache:
        _schema_cache[db_name] = registry_get_schema(db_name)
    return _schema_cache[db_name]


def _execute(db_name: str, sql: str) -> dict[str, Any]:
    """Execute against a registered DB, with safe-query gating."""
    if db_name == "ecommerce":
        return execute_local_query(sql)
    # Fallback for other registered DBs (mirrors db.execute_query semantics)
    from db import is_safe_query
    if not is_safe_query(sql):
        return {
            "error": "Only SELECT statements are allowed.",
            "columns": [],
            "results": [],
        }
    conn = registry_conn(db_name)
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [list(r) for r in cur.fetchall()]
        return {"columns": cols, "results": rows, "error": None}
    except Exception as e:  # noqa: BLE001
        return {"columns": [], "results": [], "error": str(e)}
    finally:
        conn.close()


# ── Routes: UI ─────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(content=_HTML_PATH.read_text(encoding="utf-8"))


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "model": settings.MODEL, "version": app.version}


# ── Routes: Query ──────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
async def query(body: QueryRequest) -> QueryResponse:
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    db_name = body.db_name or "ecommerce"
    schema = _schema_for(db_name)

    t0 = time.perf_counter()
    try:
        sql = generate_sql(question, schema)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Claude API error: {e}")

    valid = validate_sql(sql)
    if not valid.ok:
        dur_ms = (time.perf_counter() - t0) * 1000
        qid = history.log_query(
            db_name=db_name, question=question, sql=sql,
            row_count=0, error=valid.error, duration_ms=dur_ms,
        )
        return QueryResponse(
            sql=sql, columns=[], results=[], error=valid.error,
            row_count=0, query_id=qid, db_name=db_name, duration_ms=dur_ms,
        )

    result = _execute(db_name, sql)
    dur_ms = (time.perf_counter() - t0) * 1000

    qid = history.log_query(
        db_name=db_name,
        question=question,
        sql=sql,
        row_count=len(result["results"]),
        error=result.get("error"),
        duration_ms=dur_ms,
    )

    return QueryResponse(
        sql=sql,
        columns=result["columns"],
        results=result["results"],
        error=result.get("error"),
        row_count=len(result["results"]),
        query_id=qid,
        db_name=db_name,
        duration_ms=dur_ms,
    )


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
            "Average review rating per product category",
            "Top suppliers by total stock value",
        ]
    }


# ── Routes: Databases & Schema ─────────────────────────────────────────────

@app.get("/databases")
async def databases() -> dict:
    return {"databases": registry_list()}


@app.get("/schema")
async def schema_default() -> dict:
    return {"schema": _schema_for("ecommerce")}


@app.get("/schema/{db_name}")
async def schema_for(db_name: str) -> dict:
    try:
        return {"schema": _schema_for(db_name), "db_name": db_name}
    except DatabaseNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/schema/{db_name}/analyze", response_model=SchemaSummary)
async def schema_analyze(db_name: str) -> SchemaSummary:
    conn = registry_conn(db_name)
    try:
        return analyze_schema(conn, db_name)
    finally:
        conn.close()


@app.get("/schema/{db_name}/erd")
async def schema_erd(db_name: str) -> dict:
    conn = registry_conn(db_name)
    try:
        summary = analyze_schema(conn, db_name)
    finally:
        conn.close()
    return {"db_name": db_name, "mermaid": generate_mermaid_erd(summary)}


# ── Routes: Explain / Optimize ─────────────────────────────────────────────

class ExplainRequest(BaseModel):
    sql: str
    db_name: str = "ecommerce"


@app.post("/explain", response_model=QueryExplanation)
async def explain(body: ExplainRequest) -> QueryExplanation:
    schema = _schema_for(body.db_name)
    return ai_explain_query(body.sql, schema)


@app.post("/optimize", response_model=OptimizationSuggestion)
async def optimize(body: ExplainRequest) -> OptimizationSuggestion:
    schema = _schema_for(body.db_name)
    return ai_optimize_query(body.sql, schema)


# ── Routes: Charts ─────────────────────────────────────────────────────────

class ChartSuggestRequest(BaseModel):
    columns: list[str]
    rows: list[list[Any]]


@app.post("/chart-suggest", response_model=ChartConfig)
async def chart_suggest(body: ChartSuggestRequest) -> ChartConfig:
    return suggest_chart(body.columns, body.rows)


# ── Routes: Export ─────────────────────────────────────────────────────────

@app.post("/export/{format}")
async def export_results(format: str, body: ExportRequest) -> Response:
    try:
        data = export(format, body.columns, body.rows)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    fmt = format.lower()
    ext = EXTENSIONS.get(fmt, fmt)
    ctype = CONTENT_TYPES.get(fmt, "application/octet-stream")
    fname = f"{body.filename}.{ext}"
    return Response(
        content=data,
        media_type=ctype,
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


# ── Routes: History ────────────────────────────────────────────────────────

@app.get("/history", response_model=list[QueryHistoryRecord])
async def history_list(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[QueryHistoryRecord]:
    return history.list_history(limit=limit, offset=offset)


@app.get("/history/search", response_model=list[QueryHistoryRecord])
async def history_search(q: str, limit: int = 50) -> list[QueryHistoryRecord]:
    return history.search_history(q, limit=limit)


@app.get("/history/{qid}", response_model=QueryHistoryRecord)
async def history_get(qid: int) -> QueryHistoryRecord:
    rec = history.get_query(qid)
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    return rec


@app.delete("/history/{qid}")
async def history_delete(qid: int) -> dict:
    ok = history.delete_history(qid)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": qid}


# ── Routes: Saved queries ──────────────────────────────────────────────────

class SavedQueryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    db_name: str = "ecommerce"
    sql: str
    description: str | None = None


@app.post("/saved", response_model=SavedQuery)
async def saved_create(body: SavedQueryCreate) -> SavedQuery:
    return history.save_query(
        name=body.name, db_name=body.db_name,
        sql=body.sql, description=body.description,
    )


@app.get("/saved", response_model=list[SavedQuery])
async def saved_list() -> list[SavedQuery]:
    return history.list_saved()


@app.get("/saved/{sid}", response_model=SavedQuery)
async def saved_get(sid: int) -> SavedQuery:
    rec = history.get_saved(sid)
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    return rec


@app.delete("/saved/{sid}")
async def saved_delete(sid: int) -> dict:
    ok = history.delete_saved(sid)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": sid}


# ── Routes: Follow-up questions ────────────────────────────────────────────

class FollowupRequest(BaseModel):
    question: str
    columns: list[str]
    rows: list[list[Any]]


@app.post("/followup", response_model=list[NLFollowUp])
async def followup(body: FollowupRequest) -> list[NLFollowUp]:
    return suggest_followup_questions(body.question, body.columns, body.rows)
