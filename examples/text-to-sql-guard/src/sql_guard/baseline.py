"""The keyword filter most text-to-SQL tutorials start with. Used as a baseline."""
from __future__ import annotations

import re

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|truncate|vacuum)\b",
    re.IGNORECASE,
)


def keyword_guard(sql: str) -> tuple[bool, str]:
    """Allow only text that starts with SELECT and contains no write keyword."""
    text = sql.strip().rstrip(";").strip()
    if not text.lower().startswith("select"):
        return False, "does not start with SELECT"
    if ";" in text:
        return False, "multiple statements"
    match = _FORBIDDEN.search(text)
    if match:
        return False, f"forbidden keyword {match.group(0)!r}"
    return True, "ok"
