"""Offline, independently verified correction memory: educational example.

No model weights are updated. The offline model and task oracle are synthetic.
This is NOT an authenticated memory store or a safe general-purpose instruction system.
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
MAX_CAPACITY = 10000
MAX_TEXT = 2000
SOURCES = frozenset({"test", "human", "tool"})


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT:
        raise ValueError(f"{field} must contain 1-{MAX_TEXT} characters")
    return value


@dataclass(frozen=True)
class Verdict:
    passed: bool
    corrected_answer: str | None = None
    guidance: str | None = None
    source: str = "test"


def _checked_verdict(value: object) -> Verdict:
    if not isinstance(value, Verdict) or type(value.passed) is not bool:
        raise TypeError("verifier must return Verdict with a boolean passed")
    return value


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
        if type(capacity) is not int or not 1 <= capacity <= MAX_CAPACITY:
            raise ValueError("capacity must be an integer between 1 and 10000")
        self.capacity = capacity
        self.lessons: list[Lesson] = []

    def record(self, lesson: Lesson, verifier: Callable[[str, str], Verdict]) -> bool:
        """Re-check an answer before storage; trusted verifier is caller-owned."""
        if not isinstance(lesson, Lesson):
            raise TypeError("expected a Lesson")
        if lesson.source not in SOURCES:
            raise ValueError("unsupported verifier provenance")
        for field in ("scope", "question", "wrong_answer", "corrected_answer", "guidance"):
            _nonempty(getattr(lesson, field), field)
        if lesson.wrong_answer == lesson.corrected_answer:
            raise ValueError("correction did not change answer")
        checked = _checked_verdict(verifier(lesson.question, lesson.corrected_answer))
        if not checked.passed:
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
        _nonempty(question, "question")
        _nonempty(scope, "scope")
        if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")
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
        """Atomic local JSON save; neither encrypted nor tamper-authenticated."""
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
    def load(cls, path: str | Path, verifier: Callable[[str, str], Verdict]) -> VerifiedMemory:
        """Fail closed when any persisted correction fails independent re-validation.

        A valid correction does not authenticate who wrote the file or the
        guidance text. Do not load a file from an untrusted source.
        """
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema") != 1 or not isinstance(data.get("lessons"), list):
            raise ValueError("unsupported memory format")
        result = cls(capacity=data["capacity"])
        if len(data["lessons"]) > result.capacity:
            raise ValueError("memory exceeds capacity")
        for raw in data["lessons"]:
            if not isinstance(raw, dict):
                raise ValueError("lesson must be a JSON object")
            lesson = Lesson(**raw)
            if not result.record(lesson, verifier):
                raise ValueError("persisted lesson failed verification or was duplicated")
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
    """Deliberately flawed stand-in, not an LLM. Follows ANY retrieved lesson."""
    match = WORD_PAIR.fullmatch(question)
    if match is None:
        return "unsupported task"
    return match.group(2) if lessons else match.group(1)


def solve(question: str, model: Callable[[str, list[Lesson]], str],
          verifier: Callable[[str, str], Verdict], memory: VerifiedMemory,
          scope: str, *, use_memory: bool = True) -> dict[str, object]:
    lessons = memory.retrieve(question, scope) if use_memory else []
    first = model(question, lessons)
    initial = _checked_verdict(verifier(question, first))
    if initial.passed or not use_memory or not initial.corrected_answer or not initial.guidance:
        return {"answer": first, "passed": initial.passed, "attempts": 1, "learned": False}
    lesson = Lesson(scope, question, first, initial.corrected_answer,
                    initial.guidance, initial.source)
    learned = memory.record(lesson, verifier)  # Re-check proposed correction.
    if not learned:
        return {"answer": first, "passed": False, "attempts": 1, "learned": False}
    retry = model(question, memory.retrieve(question, scope))
    passed = _checked_verdict(verifier(question, retry)).passed
    return {"answer": retry, "passed": passed, "attempts": 2, "learned": True}


def evaluate(cases: list[tuple[str, str]], model: Callable[[str, list[Lesson]], str],
             memory: VerifiedMemory, scope: str, use_memory: bool,
             *, verifier: Callable[[str, str], Verdict]) -> dict[str, int]:
    """Validate gold labels and score with independent verifier; not an ML study."""
    training = {(l.scope, l.question.casefold()) for l in memory.lessons}
    if any((scope, question.casefold()) in training for question, _ in cases):
        raise ValueError("evaluation leakage: training prompt in held-out set")
    correct = 0
    for question, expected in cases:
        if not _checked_verdict(verifier(question, expected)).passed:
            raise ValueError("held-out label is not independently verified")
        answer = model(question, memory.retrieve(question, scope) if use_memory else [])
        correct += int(_checked_verdict(verifier(question, answer)).passed)
    return {"correct": correct, "total": len(cases)}


def main() -> None:
    memory = VerifiedMemory()
    training = "Last word: green purple"
    heldout = [("Last word: cyan orange", "orange"),
               ("Last word: gold silver", "silver")]
    before = evaluate(heldout, toy_model, memory, "demo", False, verifier=oracle)
    feedback = solve(training, toy_model, oracle, memory, "demo")
    after = evaluate(heldout, toy_model, memory, "demo", True, verifier=oracle)
    print(json.dumps({"demo": "synthetic deterministic; NOT a live-LLM benchmark",
                      "feedback": feedback, "memory_off": before, "memory_on": after}, indent=2))


if __name__ == "__main__":
    main()
