"""Optional: ask an OpenAI-compatible chat endpoint for SQL (standard library only)."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

from .policy import Policy, default_policy

SYSTEM = (
    "You translate questions into one SQLite SELECT statement. "
    "Use only the tables and columns listed. Reply with SQL only, no explanation."
)


def load_dotenv(path: str | Path = ".env") -> None:
    path = Path(path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def schema_prompt(policy: Policy) -> str:
    """Describe only what the policy allows, so the model is not shown PII columns."""
    return "\n".join(
        f"{table}({', '.join(sorted(c for c in cols if c))})" for table, cols in policy.tables.items()
    )


def extract_sql(text: str) -> str:
    fence = re.search(r"```(?:sql)?\s*\n(.*?)```", text, flags=re.S | re.I)
    return (fence.group(1) if fence else text).strip()


def generate_sql(question: str, policy: Policy | None = None) -> str:
    load_dotenv()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY in .env (see .env.example).")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    policy = policy or default_policy()
    body = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM + "\n\nSchema:\n" + schema_prompt(policy)},
            {"role": "user", "content": question},
        ],
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    return extract_sql(data["choices"][0]["message"]["content"])
