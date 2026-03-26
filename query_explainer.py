"""
Translate a SQL query into a plain-English explanation using Claude.
"""

from __future__ import annotations

import anthropic

from config import settings
from models import QueryExplanation
from prompts import QUERY_EXPLAINER_SYSTEM

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def explain_query(sql: str, schema: str = "") -> QueryExplanation:
    """Return a plain-English explanation of `sql`."""
    client = _get_client()

    user_blocks = []
    if schema:
        user_blocks.append({
            "type": "text",
            "text": f"Database schema (for reference):\n```sql\n{schema}\n```",
            "cache_control": {"type": "ephemeral"},
        })
    user_blocks.append({
        "type": "text",
        "text": f"Explain this SQL query:\n```sql\n{sql}\n```",
    })

    response = client.messages.create(
        model=settings.MODEL,
        max_tokens=600,
        system=QUERY_EXPLAINER_SYSTEM,
        messages=[{"role": "user", "content": user_blocks}],
    )
    text = response.content[0].text.strip() if response.content else ""
    return QueryExplanation(sql=sql, explanation=text)
