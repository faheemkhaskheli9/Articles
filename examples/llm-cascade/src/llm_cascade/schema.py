"""Fields we extract from a job posting, their allowed values and the words that signal them."""
from __future__ import annotations

from dataclasses import dataclass

FIELDS: dict[str, tuple[str, ...]] = {
    "visa_sponsorship": ("yes", "no", "unknown"),
    "work_mode": ("remote", "hybrid", "onsite", "unknown"),
    "german": ("required", "preferred", "not_required"),
}

# Value to use when the posting never mentions the topic at all.
DEFAULT_WHEN_ABSENT: dict[str, str] = {
    "visa_sponsorship": "unknown",
    "work_mode": "unknown",
    "german": "not_required",
}

# A sentence that contains one of these words is "about" the field.
CUES: dict[str, tuple[str, ...]] = {
    "visa_sponsorship": ("visa", "sponsor", "work permit", "right to work", "authorized to work",
                         "authorised to work", "blue card", "relocation", "migrant"),
    "work_mode": ("remote", "hybrid", "on-site", "onsite", "office", "in person", "in-person",
                  "work from home", "home office", "work from anywhere"),
    "german": ("german", "deutsch"),
}


@dataclass(frozen=True)
class FieldResult:
    value: str
    evidence: str
    tier: str  # "rules", "local", "remote" or "review"
