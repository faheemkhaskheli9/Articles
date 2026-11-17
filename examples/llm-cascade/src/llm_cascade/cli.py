"""Command line: demo, evaluate, extract."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .backends import Cache, from_env
from .cascade import Cascade
from .evaluate import cascade_report, format_rules, load, rules_report


def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _backends(use_local: bool, use_remote: bool) -> list:
    cache = Cache(os.getenv("CASCADE_CACHE", ".cache/llm_cascade.sqlite"))
    out = []
    for tier, wanted in (("local", use_local), ("remote", use_remote)):
        if not wanted:
            continue
        backend = from_env(tier, cache)
        if backend is None:
            sys.exit(f"--{tier} needs {tier.upper()}_BASE_URL and {tier.upper()}_MODEL (see .env.example)")
        out.append(backend)
    return out


def cmd_demo(_: argparse.Namespace) -> None:
    row = next(r for r in load("postings") if r["id"] == "job-08")
    print(row["text"].split("\n")[0], "\n")
    out = Cascade([]).run(row["text"])
    for f, r in out.results.items():
        if r.tier == "review":
            print(f"{f:17} -> next tier (rules abstained)")
        else:
            print(f"{f:17} {r.value:12} [rules] {r.evidence}")


def cmd_evaluate(args: argparse.Namespace) -> None:
    backends = _backends(args.local, args.remote)
    report = {}
    for name in ("postings", "holdout"):
        rows = load(name)
        report[name] = {}
        for trust in (True, False):
            r = rules_report(rows, trust)
            report[name][f"trust_absence={trust}"] = r
            if not args.json:
                print(format_rules(name, trust, r), "\n")
            if backends:
                c = cascade_report(rows, backends, trust)
                report[name][f"cascade trust_absence={trust}"] = c
                if not args.json:
                    print(json.dumps(c, indent=2), "\n")
    if args.json:
        print(json.dumps(report, indent=2))


def cmd_extract(args: argparse.Namespace) -> None:
    text = Path(args.file).read_text(encoding="utf-8") if args.file else args.text
    out = Cascade(_backends(args.local, args.remote), trust_absence=not args.escalate_absent).run(text)
    print(json.dumps({
        "results": {f: vars(r) for f, r in out.results.items()},
        "calls": [vars(c) for c in out.calls],
    }, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> None:
    _load_dotenv()
    p = argparse.ArgumentParser(prog="llm-cascade", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="rules tier on one posting (offline)").set_defaults(fn=cmd_demo)
    e = sub.add_parser("evaluate", help="rules coverage, errors and token cost on both datasets")
    e.add_argument("--json", action="store_true")
    x = sub.add_parser("extract", help="run the cascade on one posting")
    src = x.add_mutually_exclusive_group(required=True)
    src.add_argument("--file")
    src.add_argument("--text")
    x.add_argument("--escalate-absent", action="store_true", help="do not trust 'topic not mentioned'")
    for sp in (e, x):
        sp.add_argument("--local", action="store_true", help="enable the local model tier")
        sp.add_argument("--remote", action="store_true", help="enable the paid model tier")
    e.set_defaults(fn=cmd_evaluate)
    x.set_defaults(fn=cmd_extract)
    args = p.parse_args(argv)
    args.fn(args)
