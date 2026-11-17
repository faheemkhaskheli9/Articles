"""Command line: tool-guard demo | check | evaluate | limitations | ask."""

from __future__ import annotations

import argparse
import json
import sys

from tool_guard.dataset import DATA, load_tasks
from tool_guard.evaluate import format_report, run
from tool_guard.guard import check_call

DEMO_TEXT = "منهنجي A-100 اڪائونٽ مان B-200 اڪائونٽ ۾ ۱۵۰۰ رپيا موڪليو."
DEMO_CALLS = {
    "correct": {"name": "bank.transfer",
                "arguments": {"from_account": "A-100", "to_account": "B-200", "amount_pkr": 1500}},
    "extra zero": {"name": "bank.transfer",
                   "arguments": {"from_account": "A-100", "to_account": "B-200", "amount_pkr": 15000}},
    "swapped": {"name": "bank.transfer",
                "arguments": {"from_account": "B-200", "to_account": "A-100", "amount_pkr": 1500}},
}


def _print(obj: object) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="tool-guard")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="Guard three proposed calls for one Sindhi request")
    check = sub.add_parser("check", help="Guard one call: TEXT and CALL_JSON")
    check.add_argument("text")
    check.add_argument("call_json")
    ev = sub.add_parser("evaluate", help="Ablation over data/tasks.jsonl")
    ev.add_argument("--json", action="store_true")
    sub.add_parser("limitations", help="Known failure cases in data/limitations.jsonl")
    ask = sub.add_parser("ask", help="Let an LLM propose a call, then guard it (.env needed)")
    ask.add_argument("text")
    args = parser.parse_args(argv)

    if args.command == "demo":
        print(f"Request: {DEMO_TEXT}\n")
        for label, call in DEMO_CALLS.items():
            print(f"--- model proposed: {label}")
            _print(check_call(DEMO_TEXT, call).to_dict())
    elif args.command == "check":
        _print(check_call(args.text, json.loads(args.call_json)).to_dict())
    elif args.command == "evaluate":
        report = run(load_tasks())
        if args.json:
            _print(report)
        else:
            print(f"{len(load_tasks())} tasks from {DATA.name}\n{format_report(report)}")
    elif args.command == "limitations":
        path = DATA.with_name("limitations.jsonl")
        for case in load_tasks(path):
            decision = check_call(case["prompt"], case["call"])
            print(f"{case['id']:<24} guard={decision.action:<8} call_correct={case['call_is_correct']}")
            print(f"  {case['why']}")
    elif args.command == "ask":
        from tool_guard.llm import load_env, propose_call

        load_env()
        call = propose_call(args.text)
        if call is None:
            print("The model proposed no tool call.")
            return 1
        print("model proposed:")
        _print(call)
        _print(check_call(args.text, call).to_dict())
    return 0
