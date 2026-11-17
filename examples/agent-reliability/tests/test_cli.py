import json
import subprocess
import sys

from agent_reliability.demo import run_examples


def test_example_execution_has_expected_failure_modes():
    result = run_examples()
    assert result["booking_duplicate"]["facts"] == {"error": "duplicate_operation"}
    assert result["transfer_without_confirmation"]["facts"] == {"error": "confirmation_required"}
    assert result["after_independent_review"]["independently_reviewed_completion"] == 0.0


def test_module_json_cli_runs():
    completed = subprocess.run([sys.executable, "-m", "agent_reliability", "--json"],
                               capture_output=True, text=True, check=True)
    report = json.loads(completed.stdout)
    assert report["unreviewed_score"]["legacy_completion"] == 1
