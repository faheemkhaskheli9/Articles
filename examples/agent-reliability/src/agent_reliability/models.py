"""Typed contracts for the deliberately small companion evaluation harness."""
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    status: Literal["success", "rejected"]
    facts: dict[str, str | int | bool]


@dataclass(frozen=True)
class Task:
    id: str
    language: str
    prompt: str
    expected_call: ToolCall
    expected_status: Literal["success", "rejected"] = "success"
    expected_facts: dict[str, str | int | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class Prediction:
    task_id: str
    tool_calls: tuple[ToolCall, ...]
    final_answer: str


@dataclass(frozen=True)
class Review:
    task_id: str
    reviewer_id: str
    # A reviewer checks the entire answer against the authoritative tool output.
    grounded: bool
    language_faithful: bool
