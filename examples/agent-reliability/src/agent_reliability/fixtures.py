"""Constructed multilingual scenarios. These are NOT real model evaluations."""
import json
from importlib.resources import files

from .models import Task, ToolCall


def load_tasks() -> list[Task]:
    raw = files("agent_reliability").joinpath("fixtures.jsonl").read_text(encoding="utf-8")
    tasks = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        record["expected_call"] = ToolCall(**record["expected_call"])
        tasks.append(Task(**record))
    ids = [task.id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate task IDs")
    return tasks
