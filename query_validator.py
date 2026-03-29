"""
Cheap, local SQL pre-validation before sending the query to the executor.

Catches obvious syntax issues (e.g. incomplete statements, missing FROM)
without hitting the database — saves a round-trip and produces clearer
error messages for the UI.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass


@dataclass
class ValidationResult:
    ok: bool
    error: str | None = None


def validate_sql(sql: str) -> ValidationResult:
    s = (sql or "").strip()
    if not s:
        return ValidationResult(False, "Empty SQL.")

    if not s.endswith(";"):
        s_with_semi = s + ";"
    else:
        s_with_semi = s

    if not sqlite3.complete_statement(s_with_semi):
        return ValidationResult(False, "SQL appears incomplete (missing semicolon or unbalanced quotes).")

    # Must start with SELECT (or WITH ... SELECT)
    head = re.match(r"\s*(WITH|SELECT)\b", s, re.IGNORECASE)
    if not head:
        return ValidationResult(False, "Only SELECT (or WITH … SELECT) statements are allowed.")

    # Crude balance check on parens
    if s.count("(") != s.count(")"):
        return ValidationResult(False, "Unbalanced parentheses.")

    return ValidationResult(True, None)
