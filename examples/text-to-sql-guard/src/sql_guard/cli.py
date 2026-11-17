"""Command line: demo, evaluate, check, limitations, ask."""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from . import evaluate, limitations, sample_db
from .baseline import keyword_guard
from .guard import GuardResult, run_guarded

DEMO = [
    "SELECT c.city, SUM(o.total_pkr) AS revenue FROM orders o JOIN customers c ON c.id = o.customer_id "
    "WHERE o.status = 'paid' GROUP BY c.city ORDER BY revenue DESC",
    "WITH old AS (SELECT id FROM orders) DELETE FROM orders WHERE id IN (SELECT id FROM old)",
    "SELECT name, email FROM customers WHERE city = 'Karachi'",
    "SELECT name FROM pragma_table_info('staff_salaries')",
    "WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM r) SELECT COUNT(*) FROM r",
]


def _db(path: str | None) -> Path:
    if path:
        p = Path(path)
        return p if p.exists() else sample_db.build(p)
    return sample_db.build(Path(tempfile.mkdtemp()) / "shop.db")


def _show(sql: str, result: GuardResult) -> None:
    print("SQL:", " ".join(sql.split()))
    if not result.allowed:
        print("  BLOCKED:", result.reason)
        return
    print("  ALLOWED:", ", ".join(result.columns))
    for row in result.rows[:5]:
        print("   ", row)
    if result.truncated:
        print("  (truncated at the row limit)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sql_guard")
    parser.add_argument("--db", help="SQLite file (created with sample data if missing)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo")
    sub.add_parser("evaluate")
    sub.add_parser("limitations")
    check = sub.add_parser("check")
    check.add_argument("sql")
    ask = sub.add_parser("ask")
    ask.add_argument("question")
    args = parser.parse_args(argv)
    db = _db(args.db)

    if args.cmd == "demo":
        for sql in DEMO:
            kw_ok, kw_reason = keyword_guard(sql)
            print(f"[keyword filter: {'allow' if kw_ok else 'block'} ({kw_reason})]")
            _show(sql, run_guarded(db, sql))
            print()
    elif args.cmd == "evaluate":
        print(evaluate.format_report(evaluate.score(db)))
    elif args.cmd == "check":
        _show(args.sql, run_guarded(db, args.sql))
    elif args.cmd == "limitations":
        for name, allowed, got, expected in limitations.run(db):
            status = "matches" if got == expected else f"off by {got - expected:+,} PKR"
            print(f"{name:<17} guard={'allow' if allowed else 'block'}  "
                  f"sum={got:,}  control={expected:,}  {status}")
    elif args.cmd == "ask":
        from .llm import generate_sql

        sql = generate_sql(args.question)
        _show(sql, run_guarded(db, sql))
    return 0


if __name__ == "__main__":
    sys.exit(main())
