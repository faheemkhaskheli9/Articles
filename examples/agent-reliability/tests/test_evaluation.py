import pytest

from agent_reliability.evaluation import evaluate_prediction, strictly_equal
from agent_reliability.fixtures import load_tasks
from agent_reliability.models import Prediction, Review, ToolCall


def example():
    return next(t for t in load_tasks() if t.id == "government-injection-en")


def test_wrong_final_answer_exposes_legacy_shortcut():
    task = example()
    prediction = Prediction(task.id, (task.expected_call,), "Your application was approved.")
    score = evaluate_prediction(task, prediction)
    assert score.tool_selection == 1
    assert score.execution_outcome == 1
    assert score.legacy_completion == 1
    assert score.independently_reviewed_completion is None
    assert score.answer_grounded is None
    human = Review(task.id, "reviewer-A", grounded=False, language_faithful=True)
    reviewed = evaluate_prediction(task, prediction, human)
    assert reviewed.independently_reviewed_completion == 0
    assert reviewed.answer_grounded is False


def test_verified_answer_requires_both_review_checks():
    task = example()
    pred = Prediction(task.id, (task.expected_call,), "Your application is under review.")
    assert evaluate_prediction(task, pred, Review(task.id, "r1", True, True)).independently_reviewed_completion == 1
    assert evaluate_prediction(task, pred, Review(task.id, "r1", True, False)).independently_reviewed_completion == 0


def test_extra_or_duplicate_calls_cannot_be_hidden():
    task = example()
    for calls in [(), (task.expected_call, task.expected_call)]:
        score = evaluate_prediction(task, Prediction(task.id, calls, "Done."))
        assert score.execution_outcome == 0
        assert score.legacy_completion == 0


def test_wrong_type_and_wrong_app_id_fail_execution():
    task = example()
    wrong = ToolCall(task.expected_call.name, {"application_id": 123})
    score = evaluate_prediction(task, Prediction(task.id, (wrong,), "Done."))
    assert score.tool_selection == 1
    assert score.parameter_accuracy == 0
    assert score.execution_outcome == 0


def test_strict_comparison_rejects_booleans_as_numbers():
    assert strictly_equal({"seats": 1}, {"seats": True}) is False
    assert strictly_equal({"items": [1]}, {"items": [1.0]}) is False


def test_identity_mismatch_fails_loudly():
    task = example()
    with pytest.raises(ValueError):
        evaluate_prediction(task, Prediction("unrelated", (task.expected_call,), "Done."))
    with pytest.raises(ValueError):
        evaluate_prediction(task, Prediction(task.id, (task.expected_call,), "Done."), Review("else", "A", True, True))


def test_four_languages_are_unverified_synthetic_variants():
    tasks = load_tasks()
    assert {t.language for t in tasks} == {"en", "sd", "sd-Latn", "ur"}
    assert len(tasks) == 4
