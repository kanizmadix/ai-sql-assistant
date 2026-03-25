"""
Natural-language → SQL translation using Claude with prompt caching.

The database schema is placed in a user-message block with
cache_control={"type": "ephemeral"} so it is cached on the first request
and served cheaply on every subsequent request.
"""

from __future__ import annotations

import anthropic

from config import settings
from prompts import SQL_GENERATOR_SYSTEM

MODEL = settings.MODEL

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def generate_sql(natural_language: str, schema: str) -> str:
    """
    Translate a natural-language question to SQL using Claude.

    The schema is passed with cache_control so it is cached after the first
    API call. Subsequent calls with the same schema hit the cache at ~0.1x
    the normal input token cost.
    """
    client = _get_client()

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Here is the database schema you must use:\n\n"
                        f"```sql\n{schema}\n```"
                    ),
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": f"Convert this question to SQL:\n{natural_language}",
                },
            ],
        }
    ]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SQL_GENERATOR_SYSTEM,
        messages=messages,
    )

    sql = response.content[0].text.strip() if response.content else ""

    if sql.startswith("```"):
        lines = sql.splitlines()
        inner = [l for l in lines if not l.strip().startswith("```")]
        sql = "\n".join(inner).strip()

    return sql
