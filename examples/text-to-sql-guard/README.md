# Text-to-SQL guard

Companion code for [Stop Asking Your LLM to Write Safe SQL. Make the Database Refuse Unsafe SQL.](https://github.com/faheemkhaskheli9/Articles/blob/main/articles/text-to-sql-guard/article.md)

Runs LLM-generated SQL under three controls that SQLite enforces itself:

1. **Read-only connection** (`mode=ro` URI): writes fail whatever the SQL says.
2. **Authorizer allow-list** (`set_authorizer`): every table, column and function is checked while the query compiles. PII columns, hidden tables, `PRAGMA`, `ATTACH` and unsafe functions are denied before anything runs.
3. **Step budget** (`set_progress_handler`): runaway queries such as endless recursive CTEs and huge cross joins are interrupted.

Standard library only. No API key needed except for the optional `ask` command. All data is synthetic.

## Setup

```bash
cd examples/text-to-sql-guard
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Run

```bash
python -m sql_guard demo          # five model outputs through the keyword filter and the guard
python -m sql_guard evaluate      # both guards on 38 labeled queries in data/cases.jsonl
python -m sql_guard limitations   # allowed-but-wrong queries and a reconciliation check
python -m sql_guard check "SELECT name, email FROM customers"
python -m pytest -q
```

Every command builds a fresh sample database in a temp folder. Use `--db shop.db` to keep one (it is created if missing).

## Optional: generate SQL with an LLM

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY` (and `OPENAI_BASE_URL` / `OPENAI_MODEL` for any OpenAI-compatible server).
3. Run `python -m sql_guard ask "Which city had the most paid revenue?"`

## VS Code

Open this folder (or the repository root) and use the Run and Debug panel. Launch configurations: demo, evaluate, limitations, check one query, ask LLM, pytest.

## Layout

```text
src/sql_guard/
  policy.py       allow-listed tables, columns, functions, row and step limits
  guard.py        read-only connection + authorizer + progress budget
  baseline.py     keyword filter used as the comparison
  evaluate.py     scores both guards on data/cases.jsonl
  limitations.py  fan-out join and missing-filter examples, reconciliation
  llm.py          optional OpenAI-compatible SQL generation
  sample_db.py    synthetic shop database
  cli.py          command line
data/cases.jsonl  38 labeled queries (12 allow, 26 block)
tests/            pytest suite, including the Medium HTML check
```

## Known limits

The guard decides whether SQL is allowed, not whether it answers the question correctly. See `python -m sql_guard limitations`. The 38 cases were written alongside the guard, so treat them as a regression suite, not a benchmark.
