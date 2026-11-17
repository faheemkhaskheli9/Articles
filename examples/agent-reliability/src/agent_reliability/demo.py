"""Runnable, entirely offline article examples and deterministic adverse cases."""
import argparse
import json
from dataclasses import asdict

from .environment import MockSession
from .evaluation import evaluate_prediction
from .fixtures import load_tasks
from .models import Prediction, Review, ToolCall


def run_examples() -> dict[str, object]:
    task = next(t for t in load_tasks() if t.id == "government-injection-en")
    # Constructed deliberately wrong text, not produced by a real LLM.
    prediction = Prediction(
        task_id=task.id,
        tool_calls=(task.expected_call,),
        final_answer="Your application has been approved.",
    )
    before = evaluate_prediction(task, prediction)
    review = Review(task_id=task.id, reviewer_id="example-human-review",
                    grounded=False, language_faithful=True)
    after = evaluate_prediction(task, prediction, review)
    government_result = MockSession().execute(task.expected_call)

    booking = ToolCall(name="booking.reserve", arguments={
        "service_id": "BUS-KHI-HYD-01", "date": "2026-12-01", "seats": 2,
    })
    booking_session = MockSession()
    first_booking = booking_session.execute(booking)
    duplicate_booking = booking_session.execute(booking)

    transfer = ToolCall(name="bank.transfer", arguments={
        "from_account": "A-100", "to_account": "B-200", "amount_pkr": 500,
    })
    bank_session = MockSession(confirmation_required=True)
    unconfirmed_transfer = bank_session.execute(transfer)

    return {
        "disclaimer": "All examples are constructed. No live LLM or service is called.",
        "government_result": asdict(government_result),
        "inaccurate_final_answer": prediction.final_answer,
        "unreviewed_score": before.as_dict(),
        "after_independent_review": after.as_dict(),
        "booking_first": asdict(first_booking),
        "booking_duplicate": asdict(duplicate_booking),
        "booking_state": booking_session.snapshot(),
        "transfer_without_confirmation": asdict(unconfirmed_transfer),
        "language_variants": sorted({task.language for task in load_tasks()}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline demonstration of AI-agent evaluation traps")
    parser.add_argument("--json", action="store_true", help="Pretty-print machine-readable scenario results")
    args = parser.parse_args()
    result = run_examples()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["disclaimer"])
        print("Invalid claim:", result["inaccurate_final_answer"])
        print("Legacy completion:", result["unreviewed_score"]["legacy_completion"])
        print("Reviewed completion:", result["after_independent_review"]["independently_reviewed_completion"])
        print("Repeated reservation:", result["booking_duplicate"])
        print("Unconfirmed transfer:", result["transfer_without_confirmation"])


if __name__ == "__main__":
    main()
