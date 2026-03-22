"""
Render a SchemaSummary as a Mermaid ER diagram string.
"""

from __future__ import annotations

from models import SchemaSummary


_TYPE_FALLBACK = "TEXT"


def _safe_name(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in s)


def generate_mermaid_erd(summary: SchemaSummary) -> str:
    """Return a Mermaid `erDiagram` string for the given schema."""
    lines: list[str] = ["erDiagram"]

    for table in summary.tables:
        tname = _safe_name(table.name)
        lines.append(f"    {tname} {{")
        for col in table.columns:
            ctype = (col.get("type") or _TYPE_FALLBACK).strip().split()[0] or _TYPE_FALLBACK
            ctype = _safe_name(ctype) or _TYPE_FALLBACK
            cname = _safe_name(col["name"])
            tags: list[str] = []
            if col.get("pk"):
                tags.append("PK")
            if any(fk["from"] == col["name"] for fk in table.foreign_keys):
                tags.append("FK")
            tag_str = f" \"{','.join(tags)}\"" if tags else ""
            lines.append(f"        {ctype} {cname}{tag_str}")
        lines.append("    }")

    for join in summary.joins:
        a = _safe_name(join.from_table)
        b = _safe_name(join.to_table)
        # many-to-one relation from child (FK side) to parent (PK side)
        lines.append(f"    {a} }}o--|| {b} : \"{join.from_column}->{join.to_column}\"")

    return "\n".join(lines)
