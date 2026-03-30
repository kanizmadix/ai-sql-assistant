"""
Heuristic chart-suggestion engine.

Picks a Chart.js-friendly chart type and axis assignment based on column
types and result shape. No ML — a few targeted rules that work well for
SELECT/aggregate queries.
"""

from __future__ import annotations

from typing import Any

from models import ChartConfig


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _column_kind(values: list[Any]) -> str:
    """Return one of: 'number', 'date', 'text', 'mixed'."""
    if not values:
        return "text"
    nums = sum(1 for v in values if _is_number(v) and v is not None)
    if nums == sum(1 for v in values if v is not None):
        return "number"
    # very simple date heuristic
    str_vals = [v for v in values if isinstance(v, str)]
    if str_vals and all(_looks_like_date(s) for s in str_vals):
        return "date"
    return "text"


def _looks_like_date(s: str) -> bool:
    if len(s) < 7:
        return False
    parts = s.replace("T", "-").replace(":", "-").replace(" ", "-").split("-")
    return len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 4


def suggest_chart(columns: list[str], rows: list[list[Any]]) -> ChartConfig:
    """Suggest a chart type and a Chart.js dataset/labels payload."""
    if not columns or not rows:
        return ChartConfig(chart_type="table", reason="No data to chart.")

    if len(columns) < 2:
        return ChartConfig(
            chart_type="table",
            reason="Need at least two columns to plot a chart.",
        )

    # Figure out per-column kind
    by_col = list(zip(*rows))
    kinds = [_column_kind(list(col)) for col in by_col]

    # Find the first numeric column for Y, prefer non-numeric for X
    y_idx = next((i for i, k in enumerate(kinds) if k == "number"), None)
    x_idx = next((i for i, k in enumerate(kinds) if k != "number"), None)

    if y_idx is None or x_idx is None or y_idx == x_idx:
        return ChartConfig(
            chart_type="table",
            reason="Could not detect a numeric Y column paired with a categorical/temporal X column.",
        )

    x_col = columns[x_idx]
    y_col = columns[y_idx]
    labels = [r[x_idx] for r in rows]
    data = [r[y_idx] if _is_number(r[y_idx]) else 0 for r in rows]

    # Choose chart type:
    if kinds[x_idx] == "date":
        ctype = "line"
        reason = "Temporal X axis detected → line chart."
    elif len(rows) <= 8 and len(set(labels)) == len(labels):
        # small categorical breakdown → pie is readable
        ctype = "pie"
        reason = "Few distinct categorical values → pie chart."
    elif len(rows) > 30 and kinds[x_idx] == "number":
        ctype = "scatter"
        reason = "Two numeric columns with many points → scatter."
    else:
        ctype = "bar"
        reason = "Categorical X with numeric Y → bar chart."

    if ctype == "scatter":
        datasets = [{
            "label": f"{y_col} vs {x_col}",
            "data": [{"x": r[x_idx], "y": r[y_idx]} for r in rows],
        }]
        return ChartConfig(
            chart_type="scatter", x=x_col, y=y_col,
            labels=[], datasets=datasets, reason=reason,
        )

    datasets = [{"label": y_col, "data": data}]
    return ChartConfig(
        chart_type=ctype, x=x_col, y=y_col,
        labels=labels, datasets=datasets, reason=reason,
    )
