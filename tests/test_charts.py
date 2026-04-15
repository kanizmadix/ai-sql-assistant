"""Tests for chart-suggestion heuristics."""

from __future__ import annotations

from charts import suggest_chart


def test_no_data_returns_table() -> None:
    cfg = suggest_chart([], [])
    assert cfg.chart_type == "table"


def test_categorical_numeric_pairs_to_bar_or_pie() -> None:
    cfg = suggest_chart(["category", "total"], [["A", 10], ["B", 20], ["C", 30]])
    assert cfg.chart_type in ("bar", "pie")
    assert cfg.x == "category"
    assert cfg.y == "total"


def test_temporal_x_to_line() -> None:
    rows = [[f"2024-01-{d:02d}", d] for d in range(1, 12)]
    cfg = suggest_chart(["day", "value"], rows)
    assert cfg.chart_type == "line"


def test_single_column_returns_table() -> None:
    cfg = suggest_chart(["only"], [[1], [2]])
    assert cfg.chart_type == "table"
