"""Queries the guard correctly allows that still give the wrong answer."""
from __future__ import annotations

from pathlib import Path

from .guard import run_guarded

CORRECT = """
SELECT p.category, SUM(i.quantity * p.unit_price_pkr) AS revenue
FROM order_items i
JOIN products p ON p.id = i.product_id
JOIN orders o ON o.id = i.order_id
WHERE o.status = 'paid'
GROUP BY p.category ORDER BY p.category
"""

# Join fan-out: an order with 3 items has its full total counted 3 times.
FAN_OUT = """
SELECT p.category, SUM(o.total_pkr) AS revenue
FROM orders o
JOIN order_items i ON i.order_id = o.id
JOIN products p ON p.id = i.product_id
WHERE o.status = 'paid'
GROUP BY p.category ORDER BY p.category
"""

# Missing business filter: refunded and cancelled orders counted as revenue.
NO_STATUS_FILTER = """
SELECT p.category, SUM(i.quantity * p.unit_price_pkr) AS revenue
FROM order_items i
JOIN products p ON p.id = i.product_id
GROUP BY p.category ORDER BY p.category
"""

CONTROL_TOTAL = "SELECT SUM(total_pkr) FROM orders WHERE status = 'paid'"


def reconcile(db_path: Path, sql: str, control_sql: str = CONTROL_TOTAL) -> tuple[int, int]:
    """Sum the answer's last column and compare it to an independent control total."""
    answer = run_guarded(db_path, sql)
    control = run_guarded(db_path, control_sql)
    if not (answer.allowed and control.allowed):
        raise ValueError("reconcile only works on allowed queries")
    return sum(row[-1] for row in answer.rows), control.rows[0][0]


def run(db_path: Path) -> list[tuple[str, bool, int, int]]:
    out = []
    for name, sql in (("correct", CORRECT), ("fan-out join", FAN_OUT), ("no status filter", NO_STATUS_FILTER)):
        allowed = run_guarded(db_path, sql).allowed
        got, expected = reconcile(db_path, sql)
        out.append((name, allowed, got, expected))
    return out
