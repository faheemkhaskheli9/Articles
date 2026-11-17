"""Rules first, then a local model, then a paid model. Each tier gets only what is left."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from .backends import Backend
from .compact import build_messages, compact_context, prompt_tokens
from .rules import extract
from .schema import FIELDS, FieldResult
from .validate import check_answer


@dataclass
class Call:
    tier: str
    fields: list[str]
    prompt_tokens: int
    accepted: list[str]
    rejected: dict[str, str]


@dataclass
class Outcome:
    results: dict[str, FieldResult]
    calls: list[Call] = field(default_factory=list)

    @property
    def needs_review(self) -> list[str]:
        return [f for f, r in self.results.items() if r.tier == "review"]


class Cascade:
    def __init__(self, backends: list[Backend] | None = None, fields: list[str] | None = None,
                 trust_absence: bool = True, compact: bool = True):
        self.backends = backends or []
        self.fields = fields or list(FIELDS)
        self.trust_absence, self.compact = trust_absence, compact

    def run(self, posting: str) -> Outcome:
        found = extract(posting, self.fields, self.trust_absence)
        results: dict[str, FieldResult] = {f: r for f, r in found.items() if r is not None}
        outcome = Outcome(results)
        pending = [f for f in self.fields if f not in results]
        for backend in self.backends:
            if not pending:
                break
            context = compact_context(posting, pending) if self.compact else posting
            messages = build_messages(context, pending)
            try:
                payload = json.loads(backend.complete(messages))
            except (json.JSONDecodeError, OSError, KeyError, IndexError, ValueError) as exc:
                outcome.calls.append(Call(backend.name, pending, prompt_tokens(messages), [],
                                          {f: f"call failed: {type(exc).__name__}" for f in pending}))
                continue
            if not isinstance(payload, dict):
                payload = {}
            accepted, rejected = [], {}
            for f in pending:
                ok, reason = check_answer(f, payload.get(f), posting)
                if ok:
                    answer = payload[f]
                    results[f] = FieldResult(answer["value"], answer.get("evidence", ""), backend.name)
                    accepted.append(f)
                else:
                    rejected[f] = reason
            outcome.calls.append(Call(backend.name, list(pending), prompt_tokens(messages), accepted, rejected))
            pending = [f for f in pending if f not in results]
        for f in pending:
            results[f] = FieldResult("needs_review", "", "review")
        outcome.results = {f: results[f] for f in self.fields}
        return outcome
