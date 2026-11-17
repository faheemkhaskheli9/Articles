"""Offline, independently verified correction memory: educational example.

No model weights are updated. The offline model and task oracle are synthetic.
Do not use this file as a secure multi-tenant service.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

WORD_PAIR = re.compile(r"^Last word:\s*([a-z]+)\s+([a-z]+)\s*$", re.I)
TOKENS = re.compile(r"[a-z]+", re.I)


@dataclass(frozen=True)
class Verdict:
    passed: bool
    corrected_answer: str | None = None
    guidance: str | None = None
    source: str = "test"


@dataclass(frozen=True)
class Lesson:
    scope: str
    question: str
    wrong_answer: str
    corrected_answer: str
    guidance: str
    source: str


class VerifiedMemory:
    def __init__(self, capacity: int = 100) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.lessons: list[Lesson] = []

    def record(self, lesson: Lesson, verifier: Callable[[str, str], Verdict]) -> bool:
        """Only persist a correction that passes a separate trusted check."""
        if lesson.source not in {"test", "human", "tool"}:
            raise ValueError("unsupported verifier provenance")
        if not all((lesson.scope, lesson.question, lesson.wrong_answer,
                    lesson.corrected_answer, lesson.guidance)):
            raise ValueError("empty correction field")
        if lesson.wrong_answer == lesson.corrected_answer:
            raise ValueError("correction did not change answer")
        checked = verifier(lesson.question, lesson.corrected_answer)
        if not isinstance(checked, Verdict) or not checked.passed:
            return False
        for existing in self.lessons:
            if (existing.scope, existing.question.casefold()) == (lesson.scope, lesson.question.casefold()):
                if existing.corrected_answer != lesson.corrected_answer:
                    raise ValueError("conflicting correction; review before replacing")
                return False
        self.lessons.append(lesson)
        del self.lessons[:-self.capacity]
        return True

    def retrieve(self, question: str, scope: str, threshold: float = 0.3) -> list[Lesson]:
        terms = set(TOKENS.findall(question.casefold()))
        matches: list[tuple[float, Lesson]] = []
        for lesson in self.lessons:
            if lesson.scope != scope:
                continue
            old_terms = set(TOKENS.findall(lesson.question.casefold()))
            score = len(terms & old_terms) / len(terms | old_terms) if terms | old_terms else 0.0
            if score >= threshold:
                matches.append((score, lesson))
        matches.sort(key=lambda item: -item[0])
        return [lesson for _, lesson in matches[:3]]

    def save(self, path: str | Path) -> None:
        """Atomic local JSON save, not encrypted or authenticated."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent,
                                             prefix=".memory-", delete=False) as handle:
                tmp_path = Path(handle.name)
                os.chmod(tmp_path, 0o600)
                json.dump({"schema": 1, "capacity": self.capacity,
                           "lessons": [asdict(lesson) for lesson in self.lessons]}, handle)
            os.replace(tmp_path, target)
        finally:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()

    @classmethod
    def load(cls, path: str | Path) -> VerifiedMemory:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("schema") != 1 or not isinstance(data.get("lessons"), list):
            raise ValueError("unsupported memory format")
        result = cls(capacity=data["capacity"])
        result.lessons = [Lesson(**item) for item in data["lessons"]]
        if len(result.lessons) > result.capacity:
            raise ValueError("memory exceeds capacity")
        return result


def oracle(question: str, answer: str) -> Verdict:
    """Independent task contract for the *synthetic* last-word task."""
    match = WORD_PAIR.fullmatch(question)
    if match is None:
        return Verdict(False)  # No ground truth: refuse to learn.
    expected = match.group(2)
    if answer.strip().casefold() == expected.casefold():
        return Verdict(True)
    return Verdict(False, expected, "For this task return only the second (last) word.")


def toy_model(question: str, lessons: list[Lesson]) -> str:
    """Deliberately flawed stand-in, not an LLM."""
    match = WORD_PAIR.fullmatch(question)
    if match is None:
        return "unsupported task"
    return match.group(2) if lessons else match.group(1)


def solve(question: str, model: Callable[[str, list[Lesson]], str],
          verifier: Callable[[str, str], Verdict], memory: VerifiedMemory,
          scope: str, *, use_memory: bool = True) -> dict[str, object]:
    lessons = memory.retrieve(question, scope) if use_memory else []
    first = model(question, lessons)
    initial = verifier(question, first)
    if initial.passed or not use_memory or not initial.corrected_answer or not initial.guidance:
        return {"answer": first, "passed": initial.passed, "attempts": 1, "learned": False}
    lesson = Lesson(scope, question, first, initial.corrected_answer,
                    initial.guidance, initial.source)
    learned = memory.record(lesson, verifier)  # Re-check proposed correction.
    if not learned:
        return {"answer": first, "passed": False, "attempts": 1, "learned": False}
    retry = model(question, memory.retrieve(question, scope))
    return {"answer": retry, "passed": verifier(question, retry).passed,
            "attempts": 2, "learned": True}


def evaluate(cases: list[tuple[str, str]], model: Callable[[str, list[Lesson]], str],
             memory: VerifiedMemory, scope: str, use_memory: bool) -> dict[str, int]:
    """Simple frozen-task comparison, not an ML accuracy study."""
    training = {(l.scope, l.question.casefold()) for l in memory.lessons}
    if any((scope, question.casefold()) in training for question, _ in cases):
        raise ValueError("evaluation leakage: training prompt in held-out set")
    correct = sum(model(q, memory.retrieve(q, scope) if use_memory else []).strip() == expected
                  for q, expected in cases)
    return {"correct": correct, "total": len(cases)}


def main() -> None:
    memory = VerifiedMemory()
    training = "Last word: green purple"
    heldout = [("Last word: cyan orange", "orange"),
               ("Last word: gold silver", "silver")]
    before = evaluate(heldout, toy_model, memory, "demo", False)
    feedback = solve(training, toy_model, oracle, memory, "demo")
    after = evaluate(heldout, toy_model, memory, "demo", True)
    print(json.dumps({"demo": "synthetic deterministic; NOT a live-LLM benchmark",
                      "feedback": feedback, "memory_off": before, "memory_on": after}, indent=2))


if __name__ == "__main__":
    main()
