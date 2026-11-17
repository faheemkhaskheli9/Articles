"""Deterministic corruptions of a correct tool call, modelled on common tool-calling failures.

Each mutation is something the guard *should* stop. They are synthetic: they test the guard,
they are not observed model outputs.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterator
from typing import Any

from tool_guard.guard import TOOLS

Call = dict[str, Any]


def _numbers(call: Call) -> list[str]:
    return list(TOOLS[call["name"]].numbers)


def _ids(call: Call) -> list[str]:
    return list(TOOLS[call["name"]].identifiers)


def times_ten(call: Call) -> Call | None:
    """An extra zero: 1500 -> 15000 (e.g. 'pandrah sau' read as 15 thousand)."""
    if not _numbers(call):
        return None
    out = copy.deepcopy(call)
    out["arguments"][_numbers(call)[0]] *= 10
    return out


def lost_zero(call: Call) -> Call | None:
    """A dropped zero: 5000 -> 500."""
    if not _numbers(call):
        return None
    out = copy.deepcopy(call)
    name = _numbers(call)[0]
    out["arguments"][name] //= 10
    return out


def wrong_leading_digit(call: Call) -> Call | None:
    """One misread digit: 1500 -> 2500, 3450 -> 4450."""
    if not _numbers(call):
        return None
    out = copy.deepcopy(call)
    name = _numbers(call)[0]
    value = out["arguments"][name]
    out["arguments"][name] = value + 10 ** (len(str(value)) - 1)
    return out


def swapped_accounts(call: Call) -> Call | None:
    """Source and destination exchanged. Both IDs are in the text, so grounding alone passes."""
    if call["name"] != "bank.transfer":
        return None
    out = copy.deepcopy(call)
    args = out["arguments"]
    args["from_account"], args["to_account"] = args["to_account"], args["from_account"]
    return out


def wrong_identifier(call: Call) -> Call | None:
    """A near-miss ID: A-100 -> A-101."""
    out = copy.deepcopy(call)
    name = _ids(call)[0]
    value = out["arguments"][name]
    out["arguments"][name] = value[:-1] + str((int(value[-1]) + 1) % 10)
    return out


def amount_as_string(call: Call) -> Call | None:
    """'1500' instead of 1500: a schema type error."""
    if not _numbers(call):
        return None
    out = copy.deepcopy(call)
    name = _numbers(call)[0]
    out["arguments"][name] = str(out["arguments"][name])
    return out


def invented_argument(call: Call) -> Call | None:
    """An argument the schema does not have."""
    out = copy.deepcopy(call)
    out["arguments"]["note"] = "urgent"
    return out


def dropped_argument(call: Call) -> Call | None:
    out = copy.deepcopy(call)
    out["arguments"].pop(_ids(call)[0])
    return out


MUTATIONS: dict[str, Callable[[Call], Call | None]] = {
    fn.__name__: fn
    for fn in (times_ten, lost_zero, wrong_leading_digit, swapped_accounts, wrong_identifier,
               amount_as_string, invented_argument, dropped_argument)
}


def mutate(call: Call) -> Iterator[tuple[str, Call]]:
    for name, fn in MUTATIONS.items():
        mutated = fn(call)
        if mutated is not None and mutated != call:
            yield name, mutated
