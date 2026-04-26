"""Shared pytest fixtures."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

# Allow `import config`, `import history`, etc. when running from repo root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def temp_meta_db(tmp_path, monkeypatch):
    """Point history.* at a fresh, isolated metadata DB."""
    db_path = tmp_path / "meta_test.db"
    monkeypatch.setenv("META_DB_PATH", str(db_path))

    # Reload settings so the new env var takes effect
    import importlib

    import config
    importlib.reload(config)
    import history
    importlib.reload(history)

    yield history


@pytest.fixture
def sample_sqlite(tmp_path):
    """A tiny SQLite DB with a single table to use in tests."""
    p = tmp_path / "sample.db"
    conn = sqlite3.connect(p)
    conn.executescript("""
        CREATE TABLE widgets (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            qty INTEGER NOT NULL
        );
        INSERT INTO widgets (name, qty) VALUES ('a', 1), ('b', 2), ('c', 3);
    """)
    conn.commit()
    conn.close()
    return p
