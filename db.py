"""
SQLite database setup and safe query execution.
Only SELECT statements are permitted — all write operations are blocked.
"""

import re
import sqlite3
from typing import Any

DB_PATH = "ecommerce.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def is_safe_query(sql: str) -> bool:
    """
    Allow only SELECT statements. Block any DDL or DML that could mutate data.
    """
    # Strip leading/trailing whitespace and comments
    clean = sql.strip()
    # Remove single-line comments
    clean = re.sub(r"--[^\n]*", "", clean)
    # Remove multi-line comments
    clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL)
    clean = clean.strip()

    if not clean:
        return False

    # Must start with SELECT (case-insensitive)
    if not re.match(r"^SELECT\b", clean, re.IGNORECASE):
        return False

    # Block dangerous keywords that should never appear in a read-only SELECT
    forbidden = [
        r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b", r"\bUPDATE\b",
        r"\bCREATE\b", r"\bALTER\b", r"\bTRUNCATE\b", r"\bREPLACE\b",
        r"\bATTACH\b", r"\bDETACH\b", r"\bPRAGMA\b",
    ]
    for pattern in forbidden:
        if re.search(pattern, clean, re.IGNORECASE):
            return False

    return True


def execute_query(sql: str) -> dict[str, Any]:
    """
    Execute a validated SELECT query and return columns + rows.
    Returns an error dict if the query is unsafe or fails.
    """
    if not is_safe_query(sql):
        return {
            "error": "Only SELECT statements are allowed. DROP, DELETE, INSERT, UPDATE and other write operations are blocked.",
            "columns": [],
            "results": [],
        }

    try:
        conn = get_connection()
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchall()]
        conn.close()
        return {"columns": columns, "results": rows, "error": None}
    except sqlite3.Error as exc:
        return {"error": str(exc), "columns": [], "results": []}


def get_schema() -> str:
    """
    Return a human-readable schema string for all tables in the database.
    Used as context when prompting Claude.
    """
    conn = get_connection()
    schema_parts: list[str] = []

    tables_cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in tables_cursor.fetchall()]

    for table in tables:
        # Get CREATE TABLE statement
        create_cursor = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        create_row = create_cursor.fetchone()
        if create_row:
            schema_parts.append(create_row[0])

        # Get row count for context
        count_cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
        count = count_cursor.fetchone()[0]
        schema_parts.append(f"-- {table}: {count} rows\n")

    conn.close()
    return "\n\n".join(schema_parts)
