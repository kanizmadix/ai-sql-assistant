"""
Suggest follow-up natural-language questions based on the most recent
question and the result preview.
"""

from __future__ import annotations

import json
import re
from typing import Any

import anthropic

from config import settings
from models import NLFollowUp
from prompts import FOLLOWUP_SYSTEM

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def _extract_json(text: str) -> dict:
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
        return {"followups": []}


def suggest_followup_questions(
    question: str,
    columns: list[str],
    rows: list[list[Any]],
    max_preview: int = 5,
) -> list[NLFollowUp]:
    """Return 3-5 follow-up NL questions."""
    client = _get_client()

    preview = [dict(zip(columns, r)) for r in rows[:max_preview]]

    response = client.messages.create(
        model=settings.MODEL,
        max_tokens=600,
        system=FOLLOWUP_SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Original question: {question}\n\n"
                        f"Result columns: {columns}\n\n"
                        f"Result preview (first {len(preview)} rows): "
                        f"{json.dumps(preview, default=str)}"
                    ),
                },
            ],
        }],
    )

    raw = response.content[0].text if response.content else "{}"
    data = _extract_json(raw)
    items = data.get("followups") or []
    out: list[NLFollowUp] = []
    for item in items[:5]:
        if isinstance(item, dict) and item.get("question"):
            out.append(NLFollowUp(
                question=str(item["question"]),
                rationale=item.get("rationale"),
            ))
        elif isinstance(item, str):
            out.append(NLFollowUp(question=item))
    return out
