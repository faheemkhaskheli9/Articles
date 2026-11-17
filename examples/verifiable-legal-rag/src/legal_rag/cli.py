"""Command line: ask, search, evaluate, verify-fixtures."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .corpus import DEFAULT_CORPUS_DIR, PACKAGE_ROOT
from .evaluate import DEFAULT_DRAFTS, DEFAULT_QUESTIONS, evaluate_questions, evaluate_verifier
from .generation import ExtractiveGenerator, OpenAICompatibleGenerator
from .pipeline import LegalRAG
from .retrieval import DEFAULT_GLOSSARY


def load_dotenv(path: Path) -> None:
    """Minimal .env reader; existing environment variables always win."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="legal_rag", description="Verifiable legal RAG demo")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--generator", choices=["extractive", "openai"], default="extractive")
    parser.add_argument("--min-score", type=float, default=1.5)
    parser.add_argument("--min-coverage", type=float, default=0.4)
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="answer one question with verified citations")
    ask.add_argument("question")
    ask.add_argument("--json", action="store_true")
    search = sub.add_parser("search", help="show retrieval scores without generating")
    search.add_argument("query")
    ev = sub.add_parser("evaluate", help="run the answer/abstain evaluation set")
    ev.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    ev.add_argument("--json", action="store_true")
    sw = sub.add_parser("sweep", help="show how the coverage threshold trades misses for unsafe answers")
    sw.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    sw.add_argument("--values", type=float, nargs="+", default=[0.3, 0.35, 0.4, 0.45, 0.5])
    vf = sub.add_parser("verify-fixtures", help="run the verifier against adversarial drafts")
    vf.add_argument("--drafts", type=Path, default=DEFAULT_DRAFTS)
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv(PACKAGE_ROOT / ".env")
    args = build_parser().parse_args(argv)
    generator = OpenAICompatibleGenerator() if args.generator == "openai" else ExtractiveGenerator()
    rag = LegalRAG.from_files(
        args.corpus, args.glossary, generator, min_score=args.min_score, min_coverage=args.min_coverage
    )

    if args.command == "ask":
        answer = rag.ask(args.question)
        if args.json:
            print(json.dumps(answer.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(answer.render(rag.corpus))
        return 0

    if args.command == "search":
        decision = rag.retriever.retrieve(args.query)
        print(f"terms={list(decision.query_terms)} abstain={decision.abstain} reason={decision.reason}")
        for r in decision.results:
            print(f"{r.chunk.chunk_id:28} score={r.score:6.3f} coverage={r.coverage:.2f} matched={list(r.matched_terms)}")
        return 0

    if args.command == "evaluate":
        report = evaluate_questions(rag, args.questions)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        for r in report["results"]:
            print(f"{r['id']:26} {r['outcome']:24} {r['reason']:34} {','.join(r['citations'])}")
        print(f"\ntotals: {report['totals']}")
        print(f"unsafe answers: {report['unsafe_answers']} of {report['cases']}")
        for lang, counts in report["by_language"].items():
            print(f"  {lang:8} {counts}")
        return 0

    if args.command == "sweep":
        print("min_coverage  correct  abstain_ok  unsafe  missed")
        for value in args.values:
            rag.retriever.min_coverage = value
            t = evaluate_questions(rag, args.questions)["totals"]
            unsafe = t["wrong_source"] + t["answered_should_abstain"]
            print(f"{value:12.2f}  {t['correct_answer']:7}  {t['correct_abstain']:10}  {unsafe:6}  {t['missed_answer']:6}")
        return 0

    report = evaluate_verifier(rag, args.drafts)
    for r in report["results"]:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"{mark} {r['id']:24} expected={r['expected']} actual={r['actual']}")
    print(f"\n{report['passed']} of {report['cases']} fixtures produced exactly the expected issue codes")
    return 0 if report["passed"] == report["cases"] else 1


if __name__ == "__main__":
    sys.exit(main())
