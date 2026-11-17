"""Send the model only the clauses it needs, and count what that costs."""
from __future__ import annotations

import json
import math

from .rules import clauses, mentions
from .schema import FIELDS

SYSTEM_PROMPT = (
    "You extract facts from job postings. Answer only from the text. "
    "Return JSON: an object whose keys are the requested field names; each value is "
    '{"value": <one allowed value>, "evidence": <exact quote copied from the text, or "" if the text says nothing>}.'
)


def estimate_tokens(text: str) -> int:
    """Rough token count: about 4 characters per token for English text.

    Use a real tokenizer for billing. This estimate is only used to compare two prompts
    built from the same text, so the same bias applies to both.
    """
    return math.ceil(len(text) / 4)


def compact_context(text: str, fields: list[str], max_chars: int = 1200) -> str:
    """Keep clauses that mention any requested field, in order and without duplicates.

    Falls back to the start of the posting when nothing matches (for example when the
    field is escalated because no cue word was found).
    """
    seen: set[str] = set()
    kept: list[str] = []
    for clause in clauses(text):
        key = clause.lower()
        if key in seen:
            continue
        if any(mentions(f, clause) for f in fields):
            seen.add(key)
            kept.append(clause)
    context = " ".join(kept) if kept else text
    return context[:max_chars]


def build_messages(context: str, fields: list[str]) -> list[dict[str, str]]:
    allowed = {f: list(FIELDS[f]) for f in fields}
    user = f"Fields and allowed values: {json.dumps(allowed)}\n\nPosting:\n{context}"
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def prompt_tokens(messages: list[dict[str, str]]) -> int:
    return sum(estimate_tokens(m["content"]) for m in messages)
