"""Run LLM-generated SQL so that the database itself enforces the policy.

Three SQLite features do the work:

1. ``mode=ro`` URI: the connection cannot write, whatever the SQL says.
2. ``set_authorizer``: SQLite asks us about every table, column and function
   while it *compiles* the statement. Anything not on the allow-list is denied,
   so nothing runs.
3. ``set_progress_handler``: a step budget that aborts runaway queries.

Python's ``execute`` also refuses more than one statement per call.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from .policy import Policy, default_policy

_ACTION_NAMES = {
    getattr(sqlite3, f"SQLITE_{name}"): name
    for name in (
        "CREATE_INDEX CREATE_TABLE CREATE_TEMP_INDEX CREATE_TEMP_TABLE CREATE_TEMP_TRIGGER "
        "CREATE_TEMP_VIEW CREATE_TRIGGER CREATE_VIEW DELETE DROP_INDEX DROP_TABLE "
        "DROP_TEMP_INDEX DROP_TEMP_TABLE DROP_TEMP_TRIGGER DROP_TEMP_VIEW DROP_TRIGGER "
        "DROP_VIEW INSERT PRAGMA TRANSACTION UPDATE ATTACH DETACH ALTER_TABLE REINDEX "
        "ANALYZE CREATE_VTABLE DROP_VTABLE SAVEPOINT"
    ).split()
}
_ALWAYS_ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE}


@dataclass
class GuardResult:
    allowed: bool
    reason: str
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    truncated: bool = False
    denied: list[str] = field(default_factory=list)


def _authorizer(policy: Policy, denied: list[str], real_tables: set[str]):
    def check(action, arg1, arg2, _db, _trigger):
        if action in _ALWAYS_ALLOWED:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ:
            table, column = (arg1 or "").lower(), (arg2 or "").lower()
            if column in policy.tables.get(table, ()):
                return sqlite3.SQLITE_OK
            # COUNT(*) over a CTE or subquery: SQLite reports the CTE name with an
            # empty column. No stored column is exposed, so allow it.
            if column == "" and table not in real_tables:
                return sqlite3.SQLITE_OK
            denied.append(f"read {table}.{column or '*'}")
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION:
            if (arg2 or "").lower() in policy.functions:
                return sqlite3.SQLITE_OK
            denied.append(f"function {arg2}()")
            return sqlite3.SQLITE_DENY
        target = arg1 or arg2 or ""
        denied.append(f"{_ACTION_NAMES.get(action, action)} {target}".strip())
        return sqlite3.SQLITE_DENY

    return check


def connect_readonly(db_path: str | Path) -> sqlite3.Connection:
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def run_guarded(db_path: str | Path, sql: str, policy: Policy | None = None) -> GuardResult:
    """Compile and run ``sql`` under the policy. Never raises for bad SQL."""
    policy = policy or default_policy()
    denied: list[str] = []
    calls = 0

    def budget() -> int:
        nonlocal calls
        calls += 1
        return 1 if calls > policy.max_progress_calls else 0  # non-zero aborts

    con = connect_readonly(db_path)
    try:
        real_tables = {r[0].lower() for r in con.execute(
            "SELECT name FROM sqlite_schema WHERE type IN ('table', 'view')")}
        real_tables |= {"sqlite_schema", "sqlite_master", "sqlite_temp_schema", "sqlite_temp_master"}
        con.set_authorizer(_authorizer(policy, denied, real_tables))
        con.set_progress_handler(budget, policy.progress_every)
        try:
            cur = con.execute(sql)
            rows = cur.fetchmany(policy.max_rows + 1)
        except sqlite3.ProgrammingError as exc:  # e.g. two statements
            return GuardResult(False, f"rejected: {exc}")
        except sqlite3.DatabaseError as exc:
            if denied:
                return GuardResult(False, "not authorized: " + ", ".join(dict.fromkeys(denied)),
                                   denied=list(dict.fromkeys(denied)))
            if "interrupted" in str(exc):
                return GuardResult(False, "step budget exceeded (runaway query)")
            return GuardResult(False, f"invalid SQL: {exc}")
        columns = [d[0] for d in cur.description or []]
        truncated = len(rows) > policy.max_rows
        return GuardResult(True, "ok", columns, rows[: policy.max_rows], truncated)
    finally:
        con.close()
