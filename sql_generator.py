"""
Natural-language → SQL translation using Claude with prompt caching.

The database schema is placed in a user-message block with
cache_control={"type": "ephemeral"} so it is cached on the first request
and served cheaply on every subsequent request.
"""

import os
import anthropic

# Model to use — per skill defaults
MODEL = "claude-sonnet-4-6"

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


SYSTEM_PROMPT = """You are an expert SQL assistant for a SQLite e-commerce database.
Your job is to convert natural language questions into accurate, read-only SELECT queries.

Rules:
- Output ONLY the raw SQL query — no markdown, no code fences, no explanation.
- Use only SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, or any DDL.
- Use table and column names exactly as defined in the schema provided.
- Use JOINs when data from multiple tables is needed.
- Use aliases to make column names readable (e.g., c.name AS customer_name).
- For aggregations, always include a GROUP BY clause.
- Limit results to 100 rows unless the question asks for all data.
- If the question is ambiguous, write the most reasonable query.
- If the question cannot be answered with the available schema, output exactly:
  SELECT 'This question cannot be answered with the available data' AS message;
"""


def generate_sql(natural_language: str, schema: str) -> str:
    """
    Translate a natural-language question to SQL using Claude.

    The schema is passed with cache_control so it is cached after the first
    API call. Subsequent calls with the same schema hit the cache at ~0.1x
    the normal input token cost.
    """
    client = _get_client()

    # Build the messages array with cache_control on the schema block
    # so Claude caches the static schema prefix.
    messages = [
        {
            "role": "user",
            "content": [
                # Cached block: the schema (changes rarely)
                {
                    "type": "text",
                    "text": (
                        "Here is the database schema you must use:\n\n"
                        f"```sql\n{schema}\n```"
                    ),
                    "cache_control": {"type": "ephemeral"},
                },
                # Non-cached block: the user's question (changes every request)
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
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    sql = response.content[0].text.strip() if response.content else ""

    # Strip accidental markdown fences
    if sql.startswith("```"):
        lines = sql.splitlines()
        # Remove first and last fence lines
        inner = [l for l in lines if not l.strip().startswith("```")]
        sql = "\n".join(inner).strip()

    return sql
