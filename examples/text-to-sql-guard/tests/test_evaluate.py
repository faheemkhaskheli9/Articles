from sql_guard.evaluate import format_report, load_cases, score


def test_dataset_shape():
    cases = load_cases()
    assert len(cases) == 38
    assert len({c["id"] for c in cases}) == 38
    assert sum(c["expected"] == "allow" for c in cases) == 12


def test_reported_numbers(db):
    report = score(db)
    assert report["guard"]["correct"] == 38
    kw = report["keyword"]
    assert (kw["correct"], kw["unsafe_allowed"], kw["safe_blocked"]) == (18, 15, 5)
    assert "Database-enforced guard: 38/38" in format_report(report)
