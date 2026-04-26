"""
Multi-database registry.

Lets the application expose multiple SQLite files by short-name and
abstracts schema-fetch / connection-open behind a single interface.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable

from config import settings
from exceptions import DatabaseNotFound


def list_databases() -> list[dict]:
    out = []
    for name, path in settings.ALLOWED_DBS.items():
        out.append({
            "name": name,
            "path": path,
            "exists": os.path.exists(path),
            "size_bytes": os.path.getsize(path) if os.path.exists(path) else 0,
        })
    return out


def _resolve_path(name: str) -> str:
    paths = settings.ALLOWED_DBS
    if name not in paths:
        raise DatabaseNotFound(f"Unknown database '{name}'. Known: {list(paths)}")
    return paths[name]


def get_connection(name: str) -> sqlite3.Connection:
    path = _resolve_path(name)
    if not os.path.exists(path):
        raise DatabaseNotFound(f"Database file does not exist: {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_schema(name: str) -> str:
    """Human-readable schema string for a registered DB."""
    conn = get_connection(name)
    parts: list[str] = []
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()]
        for t in tables:
            row = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,),
            ).fetchone()
            if row and row[0]:
                parts.append(row[0])
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except sqlite3.Error:
                count = 0
            parts.append(f"-- {t}: {count} rows\n")
    finally:
        conn.close()
    return "\n\n".join(parts)


def names() -> Iterable[str]:
    return settings.ALLOWED_DBS.keys()
