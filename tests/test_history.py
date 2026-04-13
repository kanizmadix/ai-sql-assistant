"""Tests for the metadata DB layer."""

from __future__ import annotations


def test_log_and_list(temp_meta_db) -> None:
    h = temp_meta_db
    qid = h.log_query(
        db_name="ecommerce", question="top customers",
        sql="SELECT 1", row_count=0, error=None, duration_ms=12.5,
    )
    assert qid > 0
    rows = h.list_history(limit=10)
    assert len(rows) == 1
    assert rows[0].question == "top customers"
    assert rows[0].duration_ms == 12.5


def test_search_history(temp_meta_db) -> None:
    h = temp_meta_db
    h.log_query(db_name="ecommerce", question="how many orders", sql="SELECT COUNT(*) FROM orders", row_count=1)
    h.log_query(db_name="ecommerce", question="list customers",   sql="SELECT * FROM customers", row_count=5)
    matched = h.search_history("orders")
    assert len(matched) == 1
    assert "orders" in matched[0].question.lower()


def test_save_and_delete(temp_meta_db) -> None:
    h = temp_meta_db
    saved = h.save_query(name="topN", db_name="ecommerce", sql="SELECT 1", description="d")
    assert saved.id is not None
    assert h.get_saved(saved.id).name == "topN"
    assert h.delete_saved(saved.id) is True
    assert h.get_saved(saved.id) is None


def test_delete_history(temp_meta_db) -> None:
    h = temp_meta_db
    qid = h.log_query(db_name="ecommerce", question="x", sql="SELECT 1", row_count=0)
    assert h.delete_history(qid) is True
    assert h.delete_history(qid) is False
