"""Tests for the exporter module."""

from __future__ import annotations

import json

import pytest

from exporter import export, to_csv, to_json, to_markdown


COLUMNS = ["id", "name", "qty"]
ROWS = [[1, "a", 10], [2, "b", 20]]


def test_csv_round_trip() -> None:
    blob = to_csv(COLUMNS, ROWS).decode("utf-8")
    lines = blob.strip().splitlines()
    assert lines[0] == "id,name,qty"
    assert "a" in lines[1] and "10" in lines[1]


def test_json_export_is_list_of_dicts() -> None:
    blob = to_json(COLUMNS, ROWS).decode("utf-8")
    data = json.loads(blob)
    assert isinstance(data, list)
    assert data[0]["name"] == "a"


def test_markdown_export_has_separator_row() -> None:
    blob = to_markdown(COLUMNS, ROWS).decode("utf-8")
    assert "| --- |" in blob.replace(" ", "")
    assert "| a |" in blob


def test_excel_export_returns_bytes() -> None:
    pytest.importorskip("openpyxl")
    blob = export("excel", COLUMNS, ROWS)
    # XLSX is a zip — magic bytes are PK\x03\x04
    assert blob[:2] == b"PK"


def test_unknown_format_raises() -> None:
    with pytest.raises(ValueError):
        export("foo", COLUMNS, ROWS)
