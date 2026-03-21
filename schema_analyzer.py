"""
Schema introspection: row counts, primary keys, foreign keys, indexes,
and naive join-path suggestions.
"""

from __future__ import annotations

import sqlite3

from models import JoinSuggestion, SchemaSummary, TableInfo


def _fetchall_dicts(cursor: sqlite3.Cursor) -> list[dict]:
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def analyze_schema(conn: sqlite3.Connection, db_name: str) -> SchemaSummary:
    """Analyze a SQLite database and produce a structured SchemaSummary."""
    table_rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    tables: list[TableInfo] = []
    joins: list[JoinSuggestion] = []
    total_rows = 0

    for (tname,) in table_rows:
        cols = _fetchall_dicts(conn.execute(f"PRAGMA table_info({tname})"))
        fks = _fetchall_dicts(conn.execute(f"PRAGMA foreign_key_list({tname})"))
        idx = _fetchall_dicts(conn.execute(f"PRAGMA index_list({tname})"))

        primary_keys = [c["name"] for c in cols if c.get("pk")]

        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
        except sqlite3.Error:
            count = 0
        total_rows += count

        tables.append(TableInfo(
            name=tname,
            columns=[
                {
                    "name": c["name"],
                    "type": c["type"],
                    "notnull": bool(c.get("notnull")),
                    "default": c.get("dflt_value"),
                    "pk": bool(c.get("pk")),
                }
                for c in cols
            ],
            primary_keys=primary_keys,
            foreign_keys=[
                {
                    "from": fk["from"],
                    "to_table": fk["table"],
                    "to_column": fk["to"],
                }
                for fk in fks
            ],
            indexes=[{"name": i["name"], "unique": bool(i.get("unique"))} for i in idx],
            row_count=count,
        ))

        for fk in fks:
            joins.append(JoinSuggestion(
                from_table=tname,
                from_column=fk["from"],
                to_table=fk["table"],
                to_column=fk["to"],
            ))

    return SchemaSummary(
        db_name=db_name,
        tables=tables,
        joins=joins,
        total_rows=total_rows,
    )
