"""Score the keyword baseline and the database-enforced guard on data/cases.jsonl."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .baseline import keyword_guard
from .guard import run_guarded

DATA = Path(__file__).resolve().parents[2] / "data"


def load_cases(path: Path | None = None) -> list[dict]:
    path = path or DATA / "cases.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def score(db_path: Path, cases: list[dict] | None = None) -> dict:
    cases = cases if cases is not None else load_cases()
    out = {}
    for name in ("keyword", "guard"):
        stats = {"unsafe_allowed": 0, "safe_blocked": 0, "correct": 0}
        by_cat: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        mistakes = []
        for case in cases:
            if name == "keyword":
                allowed, reason = keyword_guard(case["sql"])
            else:
                result = run_guarded(db_path, case["sql"])
                allowed, reason = result.allowed, result.reason
            ok = allowed == (case["expected"] == "allow")
            by_cat[case["category"]][0] += ok
            by_cat[case["category"]][1] += 1
            if ok:
                stats["correct"] += 1
            else:
                stats["safe_blocked" if allowed is False else "unsafe_allowed"] += 1
                mistakes.append((case["id"], reason))
        out[name] = {**stats, "total": len(cases), "by_category": dict(by_cat), "mistakes": mistakes}
    return out


def format_report(report: dict) -> str:
    lines = []
    for name, label in (("keyword", "Keyword filter"), ("guard", "Database-enforced guard")):
        r = report[name]
        lines.append(f"{label}: {r['correct']}/{r['total']} correct, "
                     f"{r['unsafe_allowed']} unsafe allowed, {r['safe_blocked']} safe blocked")
        for cat, (ok, n) in r["by_category"].items():
            lines.append(f"  {cat:<18} {ok}/{n}")
        for case_id, reason in r["mistakes"]:
            lines.append(f"  miss {case_id}: {reason}")
    return "\n".join(lines)
