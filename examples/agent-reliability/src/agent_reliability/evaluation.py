"""Show the dangerous legacy-style shortcut and an independently reviewed gate."""
from dataclasses import asdict, dataclass

from .environment import MockSession
from .models import Prediction, Review, Task, ToolCall


def strictly_equal(expected: object, actual: object) -> bool:
    """No bool/number coercion and no nested value changes."""
    if type(expected) is not type(actual):
        return False
    if isinstance(expected, dict):
        return expected.keys() == actual.keys() and all(
            strictly_equal(v, actual[k]) for k, v in expected.items()
        )
    if isinstance(expected, list):
        return len(expected) == len(actual) and all(
            strictly_equal(left, right) for left, right in zip(expected, actual)
        )
    return expected == actual


def exact_arguments(expected: ToolCall, actual: ToolCall) -> bool:
    return expected.name == actual.name and strictly_equal(expected.arguments, actual.arguments)


@dataclass(frozen=True)
class Score:
    tool_selection: float
    parameter_accuracy: float
    execution_outcome: float
    legacy_completion: float
    independently_reviewed_completion: float | None
    answer_grounded: bool | None

    def as_dict(self) -> dict[str, float | bool | None]:
        return asdict(self)


def evaluate_prediction(task: Task, prediction: Prediction, review: Review | None = None) -> Score:
    """Execute only one call in a fresh mock session; no live transactions.

    `legacy_completion` intentionally demonstrates an evaluation weakness:
    final_answer nonempty != truthful answer. Unlike `legacy_completion`,
    reviewed completion is **unknown** without external evidence.
    """
    if task.id != prediction.task_id:
        raise ValueError("Task/prediction IDs differ")
    if review is not None and (review.task_id != task.id or not review.reviewer_id):
        raise ValueError("Human review ID mismatch or anonymous review")
    single = prediction.tool_calls[0] if len(prediction.tool_calls) == 1 else None
    chosen = float(single is not None and single.name == task.expected_call.name)
    correct_args = float(single is not None and exact_arguments(task.expected_call, single))
    result = MockSession().execute(single) if single is not None else None
    correct_outcome = float(bool(
        correct_args and result and result.status == task.expected_status
        and all(k in result.facts and strictly_equal(v, result.facts[k])
                for k, v in task.expected_facts.items())
    ))
    legacy = float(bool(correct_outcome and prediction.final_answer.strip()))
    reviewed = None if review is None else float(bool(
        legacy and review.grounded and review.language_faithful
    ))
    return Score(chosen, correct_args, correct_outcome, legacy,
                 reviewed, review.grounded if review else None)
