"""Ablation: how many correct calls pass and how many corrupted calls are stopped, per language."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from tool_guard.dataset import load_tasks
from tool_guard.guard import GuardConfig, check_call
from tool_guard.mutations import mutate

CONFIGS: dict[str, GuardConfig] = {
    "ascii-only": GuardConfig(script_digits=False, number_words=False, roles=False),
    "+script digits": GuardConfig(number_words=False, roles=False),
    "+number words": GuardConfig(roles=False),
    "full guard": GuardConfig(),
}
LANGS = ("sd", "ur", "roman", "en")


def run(tasks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    tasks = tasks if tasks is not None else load_tasks()
    report: dict[str, Any] = {}
    for label, config in CONFIGS.items():
        gold = defaultdict(lambda: [0, 0])        # lang -> [passed, total]
        caught = defaultdict(lambda: [0, 0])      # lang -> [blocked, total], served tasks only
        by_type = defaultdict(lambda: [0, 0])     # mutation -> [blocked, total]
        for task in tasks:
            lang = task["language"]
            decision = check_call(task["prompt"], task["expected_call"], config=config)
            served = decision.action != "block"
            gold[lang][0] += served
            gold[lang][1] += 1
            if not served:
                # A guard that rejects the correct call "catches" every corruption for free.
                # Count corruptions only on requests the guard can actually serve.
                continue
            for name, bad in mutate(task["expected_call"]):
                blocked = check_call(task["prompt"], bad, config=config).action == "block"
                caught[lang][0] += blocked
                caught[lang][1] += 1
                by_type[name][0] += blocked
                by_type[name][1] += 1
        report[label] = {"gold": dict(gold), "caught": dict(caught), "by_type": dict(by_type)}
    return report


def _pct(pair: list[int]) -> str:
    return f"{pair[0]}/{pair[1]} ({100 * pair[0] / pair[1]:.0f}%)" if pair[1] else "-"


def _total(d: dict[str, list[int]]) -> list[int]:
    return [sum(v[0] for v in d.values()), sum(v[1] for v in d.values())]


def format_report(report: dict[str, Any]) -> str:
    lines = []
    for label, r in report.items():
        lines.append(f"== {label}")
        lines.append(f"  correct calls allowed : {_pct(_total(r['gold']))}")
        lines.append("    " + "  ".join(f"{lang}={_pct(r['gold'][lang])}" for lang in LANGS))
        lines.append(f"  corrupted calls blocked (served requests only): {_pct(_total(r['caught']))}")
        lines.append("    " + "  ".join(f"{lang}={_pct(r['caught'].get(lang, [0, 0]))}" for lang in LANGS))
        for name, pair in r["by_type"].items():
            lines.append(f"    {name:<20} {_pct(pair)}")
    return "\n".join(lines)
