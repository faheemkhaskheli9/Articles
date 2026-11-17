import io
import json

import pytest

from sql_guard import cli, llm
from sql_guard.policy import default_policy


def test_schema_prompt_hides_blocked_columns():
    prompt = llm.schema_prompt(default_policy())
    assert "customers(city, created_at, id, name)" in prompt
    assert "email" not in prompt and "staff_salaries" not in prompt


def test_extract_sql_from_fence():
    assert llm.extract_sql("Here:\n```sql\nSELECT 1\n```\nDone") == "SELECT 1"
    assert llm.extract_sql(" SELECT 2 ") == "SELECT 2"


def test_generate_sql_calls_endpoint(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    seen = {}

    def fake_urlopen(req, timeout):
        seen["body"] = json.loads(req.data)
        reply = {"choices": [{"message": {"content": "```sql\nSELECT COUNT(*) FROM orders\n```"}}]}
        return io.BytesIO(json.dumps(reply).encode())

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    assert llm.generate_sql("how many orders?") == "SELECT COUNT(*) FROM orders"
    assert seen["body"]["temperature"] == 0


def test_generate_sql_requires_key(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        llm.generate_sql("x")


@pytest.mark.parametrize("cmd", [["demo"], ["evaluate"], ["limitations"], ["check", "SELECT COUNT(*) FROM orders"]])
def test_cli_commands(cmd, db, capsys):
    assert cli.main(["--db", str(db), *cmd]) == 0
    assert capsys.readouterr().out.strip()
