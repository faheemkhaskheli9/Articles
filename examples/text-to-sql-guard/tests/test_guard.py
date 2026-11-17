import sqlite3
from dataclasses import replace

import pytest

from sql_guard import default_policy, run_guarded
from sql_guard.guard import connect_readonly


def test_allows_join_aggregate(db):
    r = run_guarded(db, "SELECT c.city, COUNT(*) FROM orders o JOIN customers c ON c.id = o.customer_id GROUP BY c.city")
    assert r.allowed and r.columns == ["city", "COUNT(*)"] and len(r.rows) == 5


@pytest.mark.parametrize("sql, fragment", [
    ("DELETE FROM orders", "DELETE orders"),
    ("WITH x AS (SELECT 1) DELETE FROM orders", "DELETE orders"),
    ("UPDATE orders SET status = 'paid'", "UPDATE orders"),
    ("/* hi */ DELETE/**/FROM orders", "DELETE orders"),
    ("PRAGMA table_info(orders)", "PRAGMA"),
    ("SELECT email FROM customers", "read customers.email"),
    ("SELECT * FROM customers", "read customers.email"),
    ("SELECT COUNT(*) FROM staff_salaries", "read staff_salaries"),
    ("SELECT sql FROM sqlite_master", "read sqlite_master"),
    ("SELECT load_extension('x')", "function load_extension()"),
])
def test_blocks_at_compile_time(db, sql, fragment):
    r = run_guarded(db, sql)
    assert not r.allowed and fragment in r.reason


def test_nothing_is_written_when_blocked(db):
    before = run_guarded(db, "SELECT COUNT(*) FROM orders").rows
    run_guarded(db, "DELETE FROM orders")
    assert run_guarded(db, "SELECT COUNT(*) FROM orders").rows == before


def test_readonly_connection_refuses_writes_without_authorizer(db):
    con = connect_readonly(db)
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        con.execute("DELETE FROM orders")
    con.close()


def test_multiple_statements_rejected(db):
    r = run_guarded(db, "SELECT 1 FROM orders; DROP TABLE orders")
    assert not r.allowed and "one statement" in r.reason


def test_step_budget_stops_endless_recursion(db):
    r = run_guarded(db, "WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM r) SELECT COUNT(*) FROM r")
    assert not r.allowed and "budget" in r.reason


def test_bounded_recursion_and_cte_count_allowed(db):
    r = run_guarded(db, "WITH RECURSIVE m(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM m WHERE n < 12) SELECT COUNT(*) FROM m")
    assert r.allowed and r.rows == [(12,)]


def test_row_limit_truncates(db):
    r = run_guarded(db, "SELECT id FROM orders", replace(default_policy(), max_rows=10))
    assert r.allowed and len(r.rows) == 10 and r.truncated


def test_invalid_sql_is_reported(db):
    r = run_guarded(db, "SELEC id FROM orders")
    assert not r.allowed and r.reason.startswith("invalid SQL")
