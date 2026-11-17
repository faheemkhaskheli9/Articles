"""Check a model answer before trusting it. A failed check sends the field up one tier."""
from __future__ import annotations

import re

from .rules import classify, clauses, mentions
from .schema import DEFAULT_WHEN_ABSENT, FIELDS


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def check_answer(field: str, answer: object, posting: str) -> tuple[bool, str]:
    """Return (accepted, reason)."""
    if not isinstance(answer, dict):
        return False, "answer is not an object"
    value, evidence = answer.get("value"), answer.get("evidence", "")
    if value not in FIELDS[field]:
        return False, f"value {value!r} is not allowed"
    if not isinstance(evidence, str):
        return False, "evidence is not a string"
    if not evidence.strip():
        if value == DEFAULT_WHEN_ABSENT[field]:
            return True, "no evidence needed for the default value"
        return False, "non-default value without evidence"
    if _norm(evidence) not in _norm(posting):
        return False, "evidence is not a quote from the posting"
    # The quote must be about this field. A small cue list cannot cover every wording,
    # so a quote without cue words is still accepted unless a rule contradicts it.
    for clause in clauses(evidence):
        if mentions(field, clause):
            ruled = classify(field, clause)
            if ruled is not None and ruled != value:
                return False, f"rules read the evidence as {ruled!r}, model said {value!r}"
    return True, "ok"
