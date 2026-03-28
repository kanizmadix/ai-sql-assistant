"""
Suggest SQL optimizations using Claude.

Returns structured `OptimizationSuggestion` containing bullet-point hints and
optionally a rewritten faster SQL.
"""

from __future__ import annotations

import json
import re

import anthropic

from config import settings
from models import OptimizationSuggestion
from prompts import QUERY_OPTIMIZER_SYSTEM

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def _extract_json(text: str) -> dict:
    """Best-effort: pull the first {...} block out of the model's reply."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def optimize_query(sql: str, schema: str) -> OptimizationSuggestion:
    """Ask Claude to suggest optimizations for `sql` against the given schema."""
    client = _get_client()

    response = client.messages.create(
        model=settings.MODEL,
        max_tokens=900,
        system=QUERY_OPTIMIZER_SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Database schema:\n```sql\n{schema}\n```",
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": f"Review this SQL query:\n```sql\n{sql}\n```",
                },
            ],
        }],
    )

    raw = response.content[0].text if response.content else "{}"
    try:
        data = _extract_json(raw)
    except Exception:
        data = {"suggestions": ["Could not parse optimizer response"], "rewritten_sql": None}

    suggestions = data.get("suggestions") or []
    if not isinstance(suggestions, list):
        suggestions = [str(suggestions)]
    rewritten = data.get("rewritten_sql")
    if rewritten in ("", "null"):
        rewritten = None

    return OptimizationSuggestion(
        sql=sql,
        suggestions=[str(s) for s in suggestions],
        rewritten_sql=rewritten,
    )
