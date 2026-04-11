"""Tests for the SELECT-only safety guard in db.py."""

from __future__ import annotations

import pytest

from db import is_safe_query


@pytest.mark.parametrize("sql", [
    "SELECT * FROM customers",
    "select id from products limit 10",
    "  SELECT name FROM orders WHERE id=1;",
    "-- a comment\nSELECT 1",
])
def test_safe_select_passes(sql: str) -> None:
    assert is_safe_query(sql) is True


@pytest.mark.parametrize("sql", [
    "DROP TABLE customers",
    "DELETE FROM orders",
    "INSERT INTO products (name) VALUES ('x')",
    "UPDATE customers SET name='x'",
    "ALTER TABLE products ADD COLUMN x INT",
    "PRAGMA table_info(orders)",
    "ATTACH DATABASE 'foo' AS f",
    "",
    "   ",
    "SELECT 1; DROP TABLE x",
])
def test_unsafe_blocked(sql: str) -> None:
    assert is_safe_query(sql) is False
