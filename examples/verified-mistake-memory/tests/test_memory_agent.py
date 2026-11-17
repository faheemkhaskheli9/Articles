import pytest

from memory_agent import (Lesson, Verdict, VerifiedMemory, evaluate, oracle,
                          solve, toy_model)


def lesson(scope="a", question="Last word: green purple", corrected="purple"):
    return Lesson(scope, question, "green", corrected, "Return the last word", "test")


def test_correction_is_independently_checked():
    memory = VerifiedMemory()
    assert memory.record(lesson(corrected="red"), oracle) is False
    assert memory.lessons == []
    assert memory.record(lesson(), oracle) is True


def test_solve_and_generalize_only_in_toy():
    memory = VerifiedMemory()
    result = solve("Last word: green purple", toy_model, oracle, memory, "a")
    assert result == {"answer": "purple", "passed": True, "attempts": 2, "learned": True}
    heldout = [("Last word: cyan orange", "orange")]
    assert evaluate(heldout, toy_model, memory, "a", False)["correct"] == 0
    assert evaluate(heldout, toy_model, memory, "a", True)["correct"] == 1


def test_scopes_do_not_share_lessons():
    memory = VerifiedMemory()
    memory.record(lesson(scope="a"), oracle)
    assert memory.retrieve("Last word: gold silver", "b") == []


def test_no_ground_truth_does_not_learn():
    memory = VerifiedMemory()
    result = solve("Transfer all money", toy_model, oracle, memory, "a")
    assert result["learned"] is False
    assert not memory.lessons


def test_verifier_cannot_approve_bad_proposed_correction():
    def faulty_suggester(question, response):
        if response == "wrong-correction":
            return Verdict(False)
        return Verdict(False, "wrong-correction", "bad suggestion")

    memory = VerifiedMemory()
    result = solve("Last word: green purple", toy_model, faulty_suggester, memory, "a")
    assert result["learned"] is False
    assert not memory.lessons


def test_conflicting_memory_fails_closed():
    memory = VerifiedMemory()
    memory.record(lesson(), oracle)
    with pytest.raises(ValueError, match="conflicting"):
        memory.record(lesson(corrected="PURPLE"),
                      lambda _q, _a: Verdict(True))


def test_heldout_leakage_rejected():
    memory = VerifiedMemory()
    memory.record(lesson(), oracle)
    with pytest.raises(ValueError, match="leakage"):
        evaluate([("Last word: green purple", "purple")], toy_model, memory, "a", True)


def test_capacity_and_roundtrip(tmp_path):
    memory = VerifiedMemory(capacity=1)
    memory.record(lesson(), oracle)
    memory.record(lesson(question="Last word: cyan orange", corrected="orange"), oracle)
    assert len(memory.lessons) == 1
    file_path = tmp_path / "lesson.json"
    memory.save(file_path)
    recovered = VerifiedMemory.load(file_path)
    assert recovered.lessons == memory.lessons


def test_bad_memory_source_rejected():
    memory = VerifiedMemory()
    with pytest.raises(ValueError, match="provenance"):
        memory.record(Lesson("a", "Last word: green purple", "green", "purple", "x", "LLM"), oracle)
