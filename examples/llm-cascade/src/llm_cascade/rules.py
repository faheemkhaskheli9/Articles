"""Tier 1: deterministic rules that answer when they are sure and abstain when they are not.

The rules never guess. Each clause that mentions a field is classified by a small set
of patterns. The field gets a value only when every relevant clause agrees; otherwise
the rules return ``None`` and the field moves to the next tier.
"""
from __future__ import annotations

import re

from .schema import CUES, DEFAULT_WHEN_ABSENT, FieldResult

# Cues that appear in boilerplate a lot ("snacks in every office") and are ignored
# when a clear pattern elsewhere answers the field.
WEAK_CUES: dict[str, tuple[str, ...]] = {
    "visa_sponsorship": ("relocation",),
    "work_mode": ("office",),
    "german": (),
}

_CLAUSE_SPLIT = re.compile(r"(?<=[.!?;,])\s+|\n+")

_VISA_TERM = r"(?:visas?|sponsor\w*|blue card)"
_VISA_NO = [
    re.compile(r"\b(?:no|not|cannot|can't|can not|unable to|do not|don't|won't|without)\b(?:\W+\w+){0,6}?\W+" + _VISA_TERM, re.I),
    re.compile(_VISA_TERM + r"(?:\W+\w+){0,3}?\W+(?:none|not available|not provided|not offered)\b", re.I),
    re.compile(r"\bmust\b.{0,40}\b(?:right to work|authori[sz]ed to work|work permit)\b", re.I),
]
_VISA_YES = re.compile(
    r"\b(?:offer|offers|provide|provided|provides|available|support|assistance|included|yes|we sponsor)\b", re.I)

_MODE_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("onsite", re.compile(r"\b(?:not|no)\b(?:\W+\w+){0,2}?\W+remote\b|\bremote work is not possible\b", re.I)),
    ("hybrid", re.compile(
        r"\bhybrid\b|\b(?:one|two|three|four|\d)\s+office days?\b|\b(?:one|two|three|four|\d)\s+days?\s+(?:a|per)\s+week\s+in\b"
        r"|\bhome office possible\b|\b(?:work from home|home office)\b.{0,30}\bdays?\b|\d+% office", re.I)),
    ("remote", re.compile(r"\b(?:fully remote|100% remote|remote-first|remote first|work from anywhere)\b", re.I)),
    ("onsite", re.compile(r"\b(?:on-site|onsite|office-based|in person|in-person|based in our)\b", re.I)),
]

_GERMAN_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("preferred", re.compile(r"\b(?:plus|nice to have|nice-to-have|advantage|bonus|helpful|preferred|welcome)\b", re.I)),
    ("not_required", re.compile(r"\b(?:not required|not needed|not necessary)\b|\bno german\b", re.I)),
    ("required", re.compile(r"\b(?:required|mandatory|must|essential|fluent|business-fluent|native|[abc][12])\b", re.I)),
]


def clauses(text: str) -> list[str]:
    return [c.strip() for c in _CLAUSE_SPLIT.split(text) if c.strip()]


def mentions(field: str, clause: str, cues: tuple[str, ...] | None = None) -> bool:
    low = clause.lower()
    return any(cue in low for cue in (cues if cues is not None else CUES[field]))


def strong_cues(field: str) -> tuple[str, ...]:
    return tuple(c for c in CUES[field] if c not in WEAK_CUES[field])


def classify(field: str, clause: str) -> str | None:
    """Return a value for one clause, or None when the clause is unclear."""
    if field == "visa_sponsorship":
        if any(p.search(clause) for p in _VISA_NO):
            return "no"
        if re.search(_VISA_TERM, clause, re.I) and _VISA_YES.search(clause):
            return "yes"
        return None
    patterns = _MODE_PATTERNS if field == "work_mode" else _GERMAN_PATTERNS
    for value, pattern in patterns:
        if pattern.search(clause):
            return value
    return None


def extract_field(field: str, text: str, trust_absence: bool = True) -> FieldResult | None:
    """Answer one field, or return None to escalate.

    ``trust_absence=False`` escalates fields whose cue words never appear, because
    "no cue found" can also mean "the posting used words the cue list does not know".
    """
    relevant = [c for c in clauses(text) if mentions(field, c)]
    if not relevant:
        return FieldResult(DEFAULT_WHEN_ABSENT[field], "", "rules") if trust_absence else None
    answers: dict[str, str] = {}
    strong_unclear = False
    for clause in relevant:
        value = classify(field, clause)
        if value is not None:
            answers.setdefault(value, clause)
            continue
        if mentions(field, clause, strong_cues(field)):
            strong_unclear = True
    if len(answers) == 1 and not strong_unclear:
        value, clause = next(iter(answers.items()))
        return FieldResult(value, clause, "rules")
    return None  # conflicting, unclear or only weak signals: escalate


def extract(text: str, fields: list[str], trust_absence: bool = True) -> dict[str, FieldResult | None]:
    return {f: extract_field(f, text, trust_absence) for f in fields}
