"""
Pydantic v2 data models shared across the API surface.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Query --------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural-language question")
    db_name: str = Field(default="ecommerce", description="Target database name")
    max_results: int | None = Field(default=None, ge=1, le=10_000)


class QueryResponse(BaseModel):
    sql: str
    columns: list[str]
    results: list[list[Any]]
    error: str | None = None
    row_count: int = 0
    query_id: int | None = None
    db_name: str = "ecommerce"
    duration_ms: float | None = None


# ── History / saved queries --------------------------------------------------

class QueryHistoryRecord(BaseModel):
    id: int
    db_name: str
    question: str
    sql: str
    row_count: int
    error: str | None = None
    duration_ms: float | None = None
    created_at: datetime


class SavedQuery(BaseModel):
    id: int | None = None
    name: str
    db_name: str
    sql: str
    description: str | None = None
    created_at: datetime | None = None


# ── Explain / Optimize ------------------------------------------------------

class QueryExplanation(BaseModel):
    sql: str
    explanation: str


class OptimizationSuggestion(BaseModel):
    sql: str
    suggestions: list[str]
    rewritten_sql: str | None = None


# ── Charts -------------------------------------------------------------------

class ChartConfig(BaseModel):
    chart_type: Literal["bar", "line", "pie", "scatter", "table"]
    x: str | None = None
    y: str | None = None
    labels: list[Any] = Field(default_factory=list)
    datasets: list[dict[str, Any]] = Field(default_factory=list)
    reason: str | None = None


# ── Export -------------------------------------------------------------------

ExportFormat = Literal["csv", "json", "markdown", "excel"]


class ExportRequest(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    filename: str = "export"


# ── Schema -------------------------------------------------------------------

class TableInfo(BaseModel):
    name: str
    columns: list[dict[str, Any]]
    primary_keys: list[str]
    foreign_keys: list[dict[str, Any]]
    indexes: list[dict[str, Any]]
    row_count: int


class JoinSuggestion(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str


class SchemaSummary(BaseModel):
    db_name: str
    tables: list[TableInfo]
    joins: list[JoinSuggestion]
    total_rows: int


# ── Follow-up questions ------------------------------------------------------

class NLFollowUp(BaseModel):
    question: str
    rationale: str | None = None
