"""Measure what the rules tier answers, how often it is wrong, and what reaches a model."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .backends import Backend
from .cascade import Cascade
from .compact import build_messages, compact_context, prompt_tokens
from .rules import extract
from .schema import FIELDS

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load(name: str) -> list[dict]:
    path = DATA_DIR / f"{name}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rules_report(rows: list[dict], trust_absence: bool) -> dict:
    fields = list(FIELDS)
    answered = correct = 0
    wrong: list[str] = []
    escalated_postings = 0
    full_tokens = all_fields_tokens = compact_tokens = 0
    for row in rows:
        text, labels = row["text"], row["labels"]
        found = extract(text, fields, trust_absence)
        pending = [f for f, r in found.items() if r is None]
        for f, r in found.items():
            if r is None:
                continue
            answered += 1
            if r.value == labels[f]:
                correct += 1
            else:
                wrong.append(f"{row['id']}.{f}: rules={r.value} label={labels[f]}")
        all_fields_tokens += prompt_tokens(build_messages(text, fields))
        if pending:
            escalated_postings += 1
            full_tokens += prompt_tokens(build_messages(text, pending))
            compact_tokens += prompt_tokens(build_messages(compact_context(text, pending), pending))
    total = len(rows) * len(fields)
    return {
        "postings": len(rows),
        "fields": total,
        "rules_answered": answered,
        "rules_correct": correct,
        "rules_wrong": len(wrong),
        "wrong_cases": wrong,
        "escalated_fields": total - answered,
        "postings_needing_a_model": escalated_postings,
        "tokens_send_everything": all_fields_tokens,
        "tokens_escalated_full_text": full_tokens,
        "tokens_escalated_compact": compact_tokens,
    }


def cascade_report(rows: list[dict], backends: list[Backend], trust_absence: bool) -> dict:
    cascade = Cascade(backends, trust_absence=trust_absence)
    by_tier: Counter = Counter()
    correct = 0
    review: list[str] = []
    tokens: Counter = Counter()
    rejections: Counter = Counter()
    for row in rows:
        out = cascade.run(row["text"])
        for call in out.calls:
            tokens[call.tier] += call.prompt_tokens
            rejections[call.tier] += len(call.rejected)
        for f, r in out.results.items():
            by_tier[r.tier] += 1
            if r.tier == "review":
                review.append(f"{row['id']}.{f}")
            elif r.value == row["labels"][f]:
                correct += 1
    answered = sum(n for t, n in by_tier.items() if t != "review")
    return {"answered_by_tier": dict(by_tier), "correct": correct, "answered": answered,
            "needs_review": review, "prompt_tokens_by_tier": dict(tokens),
            "rejected_answers_by_tier": dict(rejections)}


def format_rules(name: str, trust_absence: bool, r: dict) -> str:
    def pct(a: int, b: int) -> str:
        return f"{100 * a / b:.0f}%" if b else "n/a"
    lines = [
        f"== {name}: {r['postings']} postings, {r['fields']} fields, trust_absence={trust_absence} ==",
        f"rules answered        {r['rules_answered']}/{r['fields']} ({pct(r['rules_answered'], r['fields'])})",
        f"rules wrong           {r['rules_wrong']}",
        f"fields escalated      {r['escalated_fields']}",
        f"postings needing a model call  {r['postings_needing_a_model']}/{r['postings']}",
        f"est. prompt tokens, every posting to a model, all fields  {r['tokens_send_everything']}",
        f"est. prompt tokens, escalated only, full text             {r['tokens_escalated_full_text']}",
        f"est. prompt tokens, escalated only, compacted             {r['tokens_escalated_compact']}"
        f" ({pct(r['tokens_escalated_compact'], r['tokens_send_everything'])} of sending everything)",
    ]
    lines += [f"  wrong: {w}" for w in r["wrong_cases"]]
    return "\n".join(lines)
