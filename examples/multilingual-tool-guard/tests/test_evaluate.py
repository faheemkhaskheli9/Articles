from tool_guard.dataset import load_tasks
from tool_guard.evaluate import CONFIGS, format_report, run
from tool_guard.mutations import mutate


def test_dataset_shape():
    tasks = load_tasks()
    assert len(tasks) == 28
    assert {t["language"] for t in tasks} == {"sd", "ur", "roman", "en"}
    assert len({t["id"] for t in tasks}) == len(tasks)


def test_mutations_always_change_the_call():
    for task in load_tasks():
        for _, bad in mutate(task["expected_call"]):
            assert bad != task["expected_call"]


def test_full_guard_on_tutorial_set():
    report = run()["full guard"]
    assert all(passed == total for passed, total in report["gold"].values())
    assert all(blocked == total for blocked, total in report["caught"].values())


def test_ascii_only_guard_rejects_most_non_english_requests():
    gold = run()["ascii-only"]["gold"]
    assert gold["sd"] == [2, 7] and gold["ur"] == [2, 7]


def test_grounding_without_roles_misses_every_swap():
    assert run()["+number words"]["by_type"]["swapped_accounts"][0] == 0


def test_report_formats_every_config():
    text = format_report(run())
    assert all(label in text for label in CONFIGS)
