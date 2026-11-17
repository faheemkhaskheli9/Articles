"""The documented limitations must stay true, or the README is lying."""
import pytest

from tool_guard.dataset import DATA, load_tasks
from tool_guard.guard import check_call

CASES = load_tasks(DATA.with_name("limitations.jsonl"))


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_documented_behavior(case):
    assert check_call(case["prompt"], case["call"]).action == case["guard_action"]
