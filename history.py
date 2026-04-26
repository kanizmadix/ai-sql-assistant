"""
Metadata store for query history, saved queries, and tags.

Uses an isolated SQLite database (META_DB_PATH) so the app's data DB stays
read-only as far as the user-facing API is concerned.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from config import settings
from models import QueryHistoryRecord, SavedQuery

_SCHEMA = """
CREATE TABLE IF NOT EXISTS query_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    db_name      TEXT    NOT NULL,
    question     TEXT    NOT NULL,
    sql          TEXT    NOT NULL,
    row_count    INTEGER NOT NULL DEFAULT 0,
    error        TEXT,
    duration_ms  REAL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_history_created ON query_history(created_at DESC);

CREATE TABLE IF NOT EXISTS saved_queries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    db_name     TEXT    NOT NULL,
    sql         TEXT    NOT NULL,
    description TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS query_tags (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id  INTEGER NOT NULL REFERENCES query_history(id) ON DELETE CASCADE,
    tag       TEXT    NOT NULL,
    UNIQUE(query_id, tag)
);
"""


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    c = sqlite3.connect(settings.META_DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        c.execute("PRAGMA foreign_keys=ON")
        yield c
        c.commit()
    finally:
        c.close()


def init_db() -> None:
    """Create metadata tables if they do not yet exist."""
    with _conn() as c:
        c.executescript(_SCHEMA)


def _row_to_history(row: sqlite3.Row) -> QueryHistoryRecord:
    return QueryHistoryRecord(
        id=row["id"],
        db_name=row["db_name"],
        question=row["question"],
        sql=row["sql"],
        row_count=row["row_count"],
        error=row["error"],
        duration_ms=row["duration_ms"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_saved(row: sqlite3.Row) -> SavedQuery:
    return SavedQuery(
        id=row["id"],
        name=row["name"],
        db_name=row["db_name"],
        sql=row["sql"],
        description=row["description"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


# ── History CRUD -------------------------------------------------------------

def log_query(
    *,
    db_name: str,
    question: str,
    sql: str,
    row_count: int,
    error: str | None = None,
    duration_ms: float | None = None,
) -> int:
    init_db()
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO query_history
               (db_name, question, sql, row_count, error, duration_ms)
               VALUES (?,?,?,?,?,?)""",
            (db_name, question, sql, row_count, error, duration_ms),
        )
        return int(cur.lastrowid)


def list_history(limit: int = 50, offset: int = 0) -> list[QueryHistoryRecord]:
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM query_history ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [_row_to_history(r) for r in rows]


def get_query(query_id: int) -> QueryHistoryRecord | None:
    init_db()
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM query_history WHERE id=?", (query_id,)
        ).fetchone()
    return _row_to_history(row) if row else None


def delete_history(query_id: int) -> bool:
    init_db()
    with _conn() as c:
        cur = c.execute("DELETE FROM query_history WHERE id=?", (query_id,))
        return cur.rowcount > 0


def search_history(q: str, limit: int = 50) -> list[QueryHistoryRecord]:
    init_db()
    like = f"%{q}%"
    with _conn() as c:
        rows = c.execute(
            """SELECT * FROM query_history
               WHERE question LIKE ? OR sql LIKE ?
               ORDER BY id DESC LIMIT ?""",
            (like, like, limit),
        ).fetchall()
    return [_row_to_history(r) for r in rows]


# ── Saved CRUD ---------------------------------------------------------------

def save_query(*, name: str, db_name: str, sql: str, description: str | None = None) -> SavedQuery:
    init_db()
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO saved_queries (name, db_name, sql, description)
               VALUES (?,?,?,?)
               ON CONFLICT(name) DO UPDATE SET
                   db_name=excluded.db_name,
                   sql=excluded.sql,
                   description=excluded.description""",
            (name, db_name, sql, description),
        )
        sid = cur.lastrowid or c.execute(
            "SELECT id FROM saved_queries WHERE name=?", (name,)
        ).fetchone()["id"]
        row = c.execute("SELECT * FROM saved_queries WHERE id=?", (sid,)).fetchone()
    return _row_to_saved(row)


def list_saved() -> list[SavedQuery]:
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM saved_queries ORDER BY id DESC"
        ).fetchall()
    return [_row_to_saved(r) for r in rows]


def get_saved(saved_id: int) -> SavedQuery | None:
    init_db()
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM saved_queries WHERE id=?", (saved_id,)
        ).fetchone()
    return _row_to_saved(row) if row else None


def delete_saved(saved_id: int) -> bool:
    init_db()
    with _conn() as c:
        cur = c.execute("DELETE FROM saved_queries WHERE id=?", (saved_id,))
        return cur.rowcount > 0


# ── Tags ---------------------------------------------------------------------

def add_tag(query_id: int, tag: str) -> None:
    init_db()
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO query_tags (query_id, tag) VALUES (?,?)",
            (query_id, tag),
        )


def list_tags(query_id: int) -> list[str]:
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT tag FROM query_tags WHERE query_id=? ORDER BY tag", (query_id,)
        ).fetchall()
    return [r["tag"] for r in rows]
