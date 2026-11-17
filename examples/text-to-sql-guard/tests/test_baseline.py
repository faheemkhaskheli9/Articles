from sql_guard.baseline import keyword_guard


def test_keyword_guard_blocks_obvious_writes():
    assert keyword_guard("DELETE FROM orders")[0] is False
    assert keyword_guard("SELECT 1; DROP TABLE x")[0] is False


def test_keyword_guard_false_positive_and_false_negative():
    assert keyword_guard('SELECT last_update AS "Last update" FROM orders')[0] is False
    assert keyword_guard("WITH x AS (SELECT 1) SELECT * FROM x")[0] is False
    assert keyword_guard("SELECT email FROM customers")[0] is True
    assert keyword_guard("SELECT load_extension('/tmp/x.so')")[0] is True
