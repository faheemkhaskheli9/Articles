from sql_guard import limitations


def test_wrong_answers_pass_the_guard_but_fail_reconciliation(db):
    rows = {name: (allowed, got, expected) for name, allowed, got, expected in limitations.run(db)}
    assert all(allowed for allowed, _, _ in rows.values())
    assert rows["correct"][1] == rows["correct"][2] == 1_883_550
    assert rows["fan-out join"][1] == 4_242_800
    assert rows["no status filter"][1] == 2_474_200
