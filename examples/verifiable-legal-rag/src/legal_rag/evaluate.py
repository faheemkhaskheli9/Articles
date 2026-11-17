"""Score answer/abstain behaviour by language, and the verifier against bad drafts."""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .corpus import DEFAULT_DATA_DIR
from .generation import parse_draft
from .pipeline import LegalRAG
from .verify import verify

DEFAULT_QUESTIONS = DEFAULT_DATA_DIR / "eval" / "questions.jsonl"
DEFAULT_DRAFTS = DEFAULT_DATA_DIR / "eval" / "adversarial_drafts.jsonl"
OUTCOMES = ("correct_answer", "correct_abstain", "wrong_source", "answered_should_abstain", "missed_answer")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{number}: {exc.msg}") from None
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path.name}: duplicate ids")
    return rows


@dataclass(frozen=True)
class CaseResult:
    id: str
    language: str
    category: str
    outcome: str
    status: str
    reason: str
    citations: tuple[str, ...]


def classify(case: dict, status: str, citations: tuple[str, ...]) -> str:
    answered = status != "abstained"
    if case["expected_status"] == "abstained":
        return "answered_should_abstain" if answered else "correct_abstain"
    if not answered:
        return "missed_answer"
    # Every cited source must be acceptable, and at least one must be cited.
    ok = bool(citations) and set(citations) <= set(case["expected_sources"])
    return "correct_answer" if ok else "wrong_source"


def evaluate_questions(rag: LegalRAG, path: Path = DEFAULT_QUESTIONS) -> dict:
    results = []
    for case in read_jsonl(path):
        answer = rag.ask(case["question"])
        outcome = classify(case, answer.status, answer.citations)
        results.append(
            CaseResult(case["id"], case["language"], case["category"], outcome,
                       answer.status, answer.reason, answer.citations)
        )
    by_language: dict[str, dict[str, int]] = defaultdict(lambda: dict.fromkeys(OUTCOMES, 0))
    for r in results:
        by_language[r.language][r.outcome] += 1
    totals = dict.fromkeys(OUTCOMES, 0)
    for r in results:
        totals[r.outcome] += 1
    unsafe = totals["wrong_source"] + totals["answered_should_abstain"]
    return {
        "cases": len(results),
        "totals": totals,
        "unsafe_answers": unsafe,
        "by_language": dict(sorted(by_language.items())),
        "results": [vars(r) | {"citations": list(r.citations)} for r in results],
    }


def evaluate_verifier(rag: LegalRAG, path: Path = DEFAULT_DRAFTS) -> dict:
    rows = []
    for case in read_jsonl(path):
        evidence = [rag.corpus[cid] for cid in case["retrieved"]]
        report = verify(parse_draft(case["draft"]), evidence, rag.corpus)
        expected = set(case["expected_codes"])
        rows.append({
            "id": case["id"],
            "expected": sorted(expected),
            "actual": sorted(report.codes),
            "passed": report.codes == expected,
        })
    return {"cases": len(rows), "passed": sum(r["passed"] for r in rows), "results": rows}
