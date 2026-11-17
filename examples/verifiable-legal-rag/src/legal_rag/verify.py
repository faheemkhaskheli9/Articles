"""Deterministic citation checks. They prove provenance, not legal correctness."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .corpus import Chunk
from .generation import DraftAnswer

MIN_QUOTE_CHARS = 25
_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
_NEGATIONS = ("not", "no", "never", "without", "except", "unless", "shall not", "nahi", "نہیں")
_NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
    "eight": "8", "nine": "9", "ten": "10", "twelve": "12", "fourteen": "14", "fifteen": "15",
    "thirty": "30", "sixty": "60", "ninety": "90",
}


@dataclass(frozen=True)
class Issue:
    claim: int
    code: str
    detail: str


@dataclass(frozen=True)
class VerificationReport:
    verified: bool
    issues: tuple[Issue, ...]

    @property
    def codes(self) -> set[str]:
        return {issue.code for issue in self.issues}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def numbers_in(text: str) -> set[str]:
    norm = normalize(text)
    found = {n.replace(",", "") for n in _NUMBER_RE.findall(norm)}
    found |= {digit for word, digit in _NUMBER_WORDS.items() if re.search(rf"\b{word}\b", norm)}
    return found


def negations_in(text: str) -> set[str]:
    norm = f" {normalize(text)} "
    return {word for word in _NEGATIONS if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", norm)}


def verify(draft: DraftAnswer, retrieved: list[Chunk], corpus: dict[str, Chunk]) -> VerificationReport:
    """Check every claim against the exact chunks the pipeline retrieved."""
    issues: list[Issue] = []
    allowed = {chunk.chunk_id: chunk for chunk in retrieved}
    if not draft.claims:
        issues.append(Issue(-1, "no_claims", "answer contains no claims"))
    for i, claim in enumerate(draft.claims):
        if not claim.text:
            issues.append(Issue(i, "empty_claim", "claim text is empty"))
        if not claim.citations:
            issues.append(Issue(i, "missing_citation", "claim cites no source"))
        if len(set(claim.citations)) != len(claim.citations):
            issues.append(Issue(i, "duplicate_citation", "same source cited twice"))
        cited: list[Chunk] = []
        for cid in claim.citations:
            if cid in allowed:
                cited.append(allowed[cid])
            elif cid in corpus:
                issues.append(Issue(i, "citation_not_retrieved", f"{cid} exists but was not in the evidence set"))
            else:
                issues.append(Issue(i, "unknown_citation", f"{cid} does not exist in the corpus"))
        quote = normalize(claim.quote)
        if len(quote) < MIN_QUOTE_CHARS:
            issues.append(Issue(i, "quote_too_short", f"quote must be at least {MIN_QUOTE_CHARS} characters"))
        elif cited and not any(quote in normalize(chunk.text) for chunk in cited):
            issues.append(Issue(i, "quote_not_found", "quote is not verbatim in any cited source"))
        extra_numbers = numbers_in(claim.text) - numbers_in(claim.quote)
        if extra_numbers:
            issues.append(Issue(i, "number_not_supported", f"numbers {sorted(extra_numbers)} absent from quote"))
        if negations_in(claim.text) != negations_in(claim.quote):
            issues.append(Issue(i, "negation_mismatch", "claim and quote differ in negation/exception words"))
    return VerificationReport(not issues, tuple(issues))
