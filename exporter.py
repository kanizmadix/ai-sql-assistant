"""
Export a result set to CSV, JSON, Markdown table, or Excel.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any


def to_csv(columns: list[str], rows: list[list[Any]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def to_json(columns: list[str], rows: list[list[Any]]) -> bytes:
    payload = [dict(zip(columns, r)) for r in rows]
    return json.dumps(payload, indent=2, default=str, ensure_ascii=False).encode("utf-8")


def to_markdown(columns: list[str], rows: list[list[Any]]) -> bytes:
    if not columns:
        return b""
    head = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body_lines = [
        "| " + " | ".join("" if v is None else str(v).replace("|", "\\|") for v in row) + " |"
        for row in rows
    ]
    md = "\n".join([head, sep, *body_lines])
    return md.encode("utf-8")


def to_excel(columns: list[str], rows: list[list[Any]]) -> bytes:
    """Build an .xlsx file in-memory using openpyxl."""
    from openpyxl import Workbook  # imported lazily

    wb = Workbook()
    ws = wb.active
    ws.title = "results"
    ws.append(columns)
    for r in rows:
        ws.append([_xl_safe(v) for v in r])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _xl_safe(v: Any) -> Any:
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    return str(v)


CONTENT_TYPES = {
    "csv": "text/csv",
    "json": "application/json",
    "markdown": "text/markdown",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

EXTENSIONS = {
    "csv": "csv",
    "json": "json",
    "markdown": "md",
    "excel": "xlsx",
}


def export(format: str, columns: list[str], rows: list[list[Any]]) -> bytes:
    fmt = format.lower()
    if fmt == "csv":
        return to_csv(columns, rows)
    if fmt == "json":
        return to_json(columns, rows)
    if fmt in ("markdown", "md"):
        return to_markdown(columns, rows)
    if fmt in ("excel", "xlsx"):
        return to_excel(columns, rows)
    raise ValueError(f"Unsupported export format: {format}")
