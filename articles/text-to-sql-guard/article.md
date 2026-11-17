# Stop Asking Your LLM to Write Safe SQL. Make the Database Refuse Unsafe SQL.

*A practical guardrail for text-to-SQL: read-only connections, a column-level allow-list enforced by the database, and a step budget, in about 100 lines of standard-library Python.*

By Faheem Khaskheli · November 17, 2026 · LLM Applications / Text-to-SQL / Python

A manager types "show me the email addresses of our Karachi customers" into your analytics chatbot. The model writes:

```sql
SELECT name, email FROM customers WHERE city = 'Karachi';
```

It is a perfect query. It starts with `SELECT`, contains no `DROP` or `DELETE`, and runs in a millisecond. It is also a privacy leak, because this chatbot was never supposed to hand out customer emails.

Most text-to-SQL tutorials protect the database with two things: a system prompt that says "only write SELECT queries" and a keyword filter that rejects `DELETE`, `DROP` and friends. The prompt is a request, not a control. The keyword filter reads the SQL as text, and SQL is not text. It is a language with comments, CTEs, table-valued functions and system tables.

I am building llm-text-to-sql, a natural-language-to-SQL pipeline with schema introspection, prompt templates and an LLM generation step. Its next phase is "validation and sandboxed execution". Before writing that phase I wanted to know what actually stops bad SQL. This article is the answer: **let the database engine enforce the policy while it compiles the query**, so nothing outside the allow-list ever runs.

The [complete runnable project](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/text-to-sql-guard) uses only the Python standard library and SQLite, runs offline, and has a 35-test pytest suite.

**Scope:** the shop database, every name, email and phone number, and all 38 test queries are synthetic and written for this tutorial.

## The problem is real, and documented

Pedro et al. studied LLM apps built on LangChain that turn user prompts into SQL. They coined the term **prompt-to-SQL (P2SQL) injection** and showed that attackers can steer the model into generating harmful SQL, and that most of the models they tested were susceptible ([ICSE 2025 paper](https://arxiv.org/abs/2308.01990)). OWASP lists the general pattern as [LLM05:2025 Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/): model output passed to a downstream system without validation. Its advice is to treat the model like any other untrusted user.

An untrusted user does not get a database login with full rights. Neither should the model.

## Where a keyword filter breaks

Here is the filter most projects start with:

```python
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|truncate|vacuum)\b",
    re.IGNORECASE,
)

def keyword_guard(sql: str) -> tuple[bool, str]:
    text = sql.strip().rstrip(";").strip()
    if not text.lower().startswith("select"):
        return False, "does not start with SELECT"
    if ";" in text:
        return False, "multiple statements"
    match = _FORBIDDEN.search(text)
    if match:
        return False, f"forbidden keyword {match.group(0)!r}"
    return True, "ok"
```

It fails in both directions.

It **blocks good queries**. LLMs often start with a comment (`-- Revenue by status`) or a CTE (`WITH paid AS (...)`). They also write friendly aliases like `last_update AS "Last update"`, and the word `update` trips the filter.

It **allows bad queries**, because nothing in them is a write keyword:

1. `SELECT name, email FROM customers` reads a column the app must never show.
2. `SELECT name FROM pragma_table_info('staff_salaries')` maps a hidden table through a table-valued function.
3. `SELECT name, sql FROM sqlite_master` dumps the whole schema.
4. `SELECT load_extension('/tmp/evil.so')` asks SQLite to load native code.
5. `SELECT COUNT(*) FROM order_items a, order_items b, order_items c` is a 64-million-row cross join.

A better regex does not fix this. The filter does not know which columns exist, what a table-valued function is, or how much work a query will do. The database does.

## The design: three controls inside the engine

SQLite gives us everything we need, and so do PostgreSQL and most server databases (see the expert notes at the end).

1. **A read-only connection.** Open the file with the URI `file:shop.db?mode=ro`. Writes fail no matter what SQL arrives. See [SQLite URI filenames](https://www.sqlite.org/uri.html).
2. **An authorizer callback.** While SQLite *compiles* a statement, it asks the callback about every table and column it reads, every function it calls and every other action (delete, pragma, attach). We answer from an allow-list. A denial aborts compilation, so the query never starts. See [sqlite3_set_authorizer](https://www.sqlite.org/c3ref/set_authorizer.html) and [Python's set_authorizer](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.set_authorizer).
3. **A step budget.** A progress handler runs every N virtual-machine instructions. Returning non-zero interrupts the query. See [sqlite3_progress_handler](https://www.sqlite.org/c3ref/progress_handler.html).

Python's `execute()` adds a fourth control for free: it refuses to run two statements in one call, so `SELECT ...; DROP TABLE ...` raises before anything happens.

For applications that run untrusted SQL, the SQLite team recommends the authorizer and the progress handler in [Defense Against the Dark Arts](https://www.sqlite.org/security.html).

## Step 1: Write the policy as an allow-list

The policy says what the chatbot may read. Everything else is denied by default.

```python
@dataclass(frozen=True)
class Policy:
    # table -> readable columns. "" is the pseudo-column SQLite reports for COUNT(*).
    tables: dict[str, frozenset[str]] = field(default_factory=dict)
    functions: frozenset[str] = frozenset()
    max_rows: int = 200
    progress_every: int = 1_000
    max_progress_calls: int = 5_000  # about 5 million VM steps


def default_policy() -> Policy:
    return Policy(
        tables={
            "customers": frozenset({"", "id", "name", "city", "created_at"}),
            "products": frozenset({"", "id", "name", "category", "unit_price_pkr"}),
            "orders": frozenset({"", "id", "customer_id", "status", "total_pkr",
                                 "last_update", "created_at"}),
            "order_items": frozenset({"", "id", "order_id", "product_id", "quantity"}),
        },
        functions=frozenset({
            "count", "sum", "avg", "min", "max", "total", "round", "abs",
            "lower", "upper", "length", "substr", "coalesce", "ifnull", "nullif",
            "date", "strftime", "like", "glob", "cast", "group_concat",
        }),
    )
```

`customers.email`, `customers.phone` and the whole `staff_salaries` table are simply absent. You never list what is forbidden, because you cannot list everything an attacker might try.

## Step 2: The authorizer callback

SQLite calls this function with an action code and up to four strings. For a column read, the action is `SQLITE_READ` and the strings are the table and column.

```python
_ALWAYS_ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE}

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
```

Three details matter here.

1. **Column reads are checked wherever they appear.** A column used only in a `WHERE`, a `JOIN`, a subquery or a string concatenation is still a read. `SELECT COUNT(*) FROM customers WHERE email LIKE '%@gmail.com'` is blocked, because filtering on a column leaks it one bit at a time.
2. **`SELECT *` expands before the callback runs.** It is checked column by column, so it fails on the first hidden column.
3. **Use `SQLITE_DENY`, not `SQLITE_IGNORE`.** Ignore silently replaces the column with NULL. The query then "works" and returns a wrong answer that nobody notices.

I found the `COUNT(*)` detail by probing the callback, not from the docs. SQLite reports `COUNT(*)` as a read of column `""`, and over a CTE it uses the CTE name as the table. The probe script is worth five minutes before you trust any authorizer rule.

## Step 3: Run the query under all three controls

```python
def connect_readonly(db_path):
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def run_guarded(db_path, sql, policy=None) -> GuardResult:
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
```

The table list is read *before* the authorizer is installed, because after that point even the guard cannot read `sqlite_schema`. Fetching `max_rows + 1` rows tells you whether the answer was cut off, so the UI can say "showing the first 200 rows" instead of presenting a partial result as complete.

Every failure comes back as a reason string. In a real pipeline that string goes back to the model as feedback ("column customers.email is not available") for one retry, and to your logs.

## Step 4: See it work

`python -m sql_guard demo` runs five model outputs through both guards. This is the real output:

```text
[keyword filter: allow (ok)]
SQL: SELECT c.city, SUM(o.total_pkr) AS revenue FROM orders o JOIN customers c ON c.id = o.customer_id WHERE o.status = 'paid' GROUP BY c.city ORDER BY revenue DESC
  ALLOWED: city, revenue
    ('Karachi', 537950)
    ('Sukkur', 393550)
    ('Lahore', 374100)
    ('Hyderabad', 350550)
    ('Islamabad', 227400)
[keyword filter: block (does not start with SELECT)]
SQL: WITH old AS (SELECT id FROM orders) DELETE FROM orders WHERE id IN (SELECT id FROM old)
  BLOCKED: not authorized: DELETE orders
[keyword filter: allow (ok)]
SQL: SELECT name, email FROM customers WHERE city = 'Karachi'
  BLOCKED: not authorized: read customers.email
[keyword filter: allow (ok)]
SQL: SELECT name FROM pragma_table_info('staff_salaries')
  BLOCKED: not authorized: read pragma_table_info.name
[keyword filter: block (does not start with SELECT)]
SQL: WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM r) SELECT COUNT(*) FROM r
  BLOCKED: step budget exceeded (runaway query)
```

Look at the last case. The keyword filter blocked it, but only because it starts with `WITH`. The same filter would also block a perfectly safe CTE. The guard blocked it for the right reason: it never ends.

## Step 5: Measure both guards on the same cases

`data/cases.jsonl` holds 38 labeled queries: 12 normal analytics questions that must be allowed, and 26 that must be blocked across seven categories (writes, stacked statements, schema discovery, PII columns, a sensitive table, runaway queries and dangerous functions). `python -m sql_guard evaluate` scores both guards. Real output, trimmed to the summary:

```text
Keyword filter: 18/38 correct, 15 unsafe allowed, 5 safe blocked
  benign             7/12
  write              6/6
  multi_statement    2/2
  schema_recon       2/5
  pii                0/5
  sensitive_table    0/2
  denial_of_service  1/3
  function           0/3
Database-enforced guard: 38/38 correct, 0 unsafe allowed, 0 safe blocked
```

The keyword filter is good at exactly what it was designed for, writes and stacked statements, and blind to everything else. It let 15 of 26 unsafe queries through and blocked 5 of 12 normal ones.

Read the 38/38 honestly. I wrote these cases and built the guard against them, so this is a **regression suite, not a benchmark**. It shows the guard handles each attack class it claims to handle, and the tests keep it that way. It does not prove there is no attack I did not think of. What makes me trust the design more than the number is *where* the decisions happen: inside the SQL compiler, which knows exactly which columns and functions a query touches, however the text is written.

Cost is small. On my machine every allowed or denied query finished in well under a millisecond after the first connection. The two runaway queries were stopped by the budget in about 20 to 35 ms.

## The failure this guard cannot catch

A guard decides whether a query is *allowed*. It cannot decide whether the query is *right*. `python -m sql_guard limitations` runs three versions of "paid revenue by product category". All three are allowed. Real output:

```text
correct           guard=allow  sum=1,883,550  control=1,883,550  matches
fan-out join      guard=allow  sum=4,242,800  control=1,883,550  off by +2,359,250 PKR
no status filter  guard=allow  sum=2,474,200  control=1,883,550  off by +590,650 PKR
```

The fan-out version joins `orders` to `order_items` and then sums `orders.total_pkr`, so an order with three items is counted three times. Revenue more than doubles. The second version forgets `status = 'paid'` and counts refunds and cancellations as income. Both are the kind of mistake a model makes on a reasonable-looking schema, and both look like normal numbers on a chart.

The example shows one cheap defense: **reconciliation**. When a question is a breakdown of a known total, sum the answer and compare it with an independent control query:

```python
CONTROL_TOTAL = "SELECT SUM(total_pkr) FROM orders WHERE status = 'paid'"

def reconcile(db_path, sql, control_sql=CONTROL_TOTAL):
    answer = run_guarded(db_path, sql)
    control = run_guarded(db_path, control_sql)
    return sum(row[-1] for row in answer.rows), control.rows[0][0]
```

Control totals come from people who know the data (finance, operations), not from the model. They catch both bugs above. They do not catch a wrong filter that happens to keep the total the same, so for important metrics the stronger fix is a **semantic layer**: define "paid revenue" once, in reviewed SQL or a metrics tool, and let the model pick metrics and dimensions instead of writing joins.

## Connect a real model

The optional `ask` command sends the question and the schema to any OpenAI-compatible Chat Completions endpoint and runs the returned SQL through the guard.

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY`, and optionally `OPENAI_BASE_URL` and `OPENAI_MODEL`.
3. Run `python -m sql_guard ask "Which city had the most paid revenue?"`

The prompt shows the model only the columns the policy allows. That makes good queries more likely, but it is not the control. If the model is tricked into asking for `email` anyway, the authorizer still refuses.

## Expert notes before you ship this

1. **Keep the policy in code or config, never in the prompt.** The prompt can be overridden by the user's text. The authorizer cannot.
2. **Map it to your production database.** In PostgreSQL the same three controls are a dedicated read-only role, column-level `GRANT SELECT (col, ...)` plus row-level security, and `statement_timeout` with `default_transaction_read_only = on`. In MySQL use a user with column privileges and `max_execution_time`. SQLite's authorizer is a good model of the idea, not a replacement for database permissions.
3. **Prefer column allow-lists to views alone.** Views are useful, but a model can still discover and query the base table if the login can read it.
4. **Set the budget from data, not a guess.** Log VM steps or execution time for real queries for a week, then put the limit well above the slowest legitimate one.
5. **Return reasons, not just "blocked".** A specific reason lets the model fix an honest mistake in one retry, and lets you spot a user who keeps probing for `salary` columns.
6. **Test with the attacks, not only the happy path.** Keep a labeled file of blocked queries like `data/cases.jsonl` and run it in CI. When you change the policy, the test tells you what you opened.

## Run it yourself

```bash
git clone https://github.com/faheemkhaskheli9/Articles.git
cd Articles/examples/text-to-sql-guard
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q
python -m sql_guard demo
python -m sql_guard evaluate
python -m sql_guard limitations
```

VS Code launch configurations for the demo, the evaluation, the limitations, a single query check, the LLM command and pytest are in `.vscode/launch.json`.

## References

1. Pedro, Castro, Carreira and Santos, [From Prompt Injections to SQL Injection Attacks: How Protected is Your LLM-Integrated Web Application?](https://arxiv.org/abs/2308.01990), published at ICSE 2025 as "Prompt-to-SQL Injections in LLM-Integrated Web Applications: Risks and Defenses".
2. OWASP, [LLM05:2025 Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/).
3. SQLite, [Compile-Time Authorization Callbacks](https://www.sqlite.org/c3ref/set_authorizer.html) and [Query Progress Callbacks](https://www.sqlite.org/c3ref/progress_handler.html).
4. SQLite, [Defense Against the Dark Arts](https://www.sqlite.org/security.html).
5. SQLite, [Uniform Resource Identifiers](https://www.sqlite.org/uri.html).
6. Python documentation, [sqlite3 Connection.set_authorizer](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.set_authorizer).
7. [Companion code for this article](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/text-to-sql-guard).
