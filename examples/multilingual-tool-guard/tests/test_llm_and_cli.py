import json

from tool_guard.cli import main
from tool_guard.llm import parse_tool_call, tool_schemas


def test_tool_schemas_are_strict():
    schema = {s["function"]["name"]: s["function"]["parameters"] for s in tool_schemas()}
    assert schema["bank_transfer"]["properties"]["amount_pkr"] == {"type": "integer"}
    assert schema["bank_transfer"]["additionalProperties"] is False


def test_parse_tool_call_maps_names_back():
    response = {"choices": [{"message": {"tool_calls": [{"function": {
        "name": "bank_transfer",
        "arguments": json.dumps({"from_account": "C-310", "to_account": "D-420", "amount_pkr": 5000})}}]}}]}
    assert parse_tool_call(response) == {
        "name": "bank.transfer",
        "arguments": {"from_account": "C-310", "to_account": "D-420", "amount_pkr": 5000}}


def test_parse_tool_call_without_call():
    assert parse_tool_call({"choices": [{"message": {"content": "hi"}}]}) is None


def test_cli_check(capsys):
    call = {"name": "bank.transfer", "arguments": {"from_account": "C-310", "to_account": "D-420", "amount_pkr": 500}}
    assert main(["check", "C-310 سے D-420 کو پانچ ہزار روپے بھیجیں۔", json.dumps(call)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["action"] == "block" and out["issues"][0]["code"] == "ungrounded_number"


def test_cli_demo_and_evaluate(capsys):
    assert main(["demo"]) == 0
    assert main(["evaluate"]) == 0
    assert main(["limitations"]) == 0
    assert "full guard" in capsys.readouterr().out
