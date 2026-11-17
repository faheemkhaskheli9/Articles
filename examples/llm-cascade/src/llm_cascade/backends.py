"""Model backends: any OpenAI-compatible chat endpoint (Ollama, vLLM, OpenAI, ...).

Standard library only. Calls are deterministic where the server allows it
(temperature 0, fixed seed) and cached in SQLite, so a repeated input costs nothing.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import urllib.request
from pathlib import Path
from typing import Callable, Protocol


class Backend(Protocol):
    name: str

    def complete(self, messages: list[dict[str, str]]) -> str: ...


class Cache:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.execute("CREATE TABLE IF NOT EXISTS calls (key TEXT PRIMARY KEY, response TEXT)")

    @staticmethod
    def key(model: str, base_url: str, messages: list[dict[str, str]]) -> str:
        raw = json.dumps([model, base_url, messages], sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, key: str) -> str | None:
        row = self.db.execute("SELECT response FROM calls WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def put(self, key: str, response: str) -> None:
        self.db.execute("INSERT OR REPLACE INTO calls VALUES (?, ?)", (key, response))
        self.db.commit()


class OpenAICompatible:
    def __init__(self, name: str, base_url: str, model: str, api_key: str = "",
                 cache: Cache | None = None, timeout: float = 120.0):
        self.name, self.base_url, self.model = name, base_url.rstrip("/"), model
        self.api_key, self.cache, self.timeout = api_key, cache, timeout
        self.cache_hits = 0

    def complete(self, messages: list[dict[str, str]]) -> str:
        key = Cache.key(self.model, self.base_url, messages)
        if self.cache and (hit := self.cache.get(key)) is not None:
            self.cache_hits += 1
            return hit
        body = json.dumps({
            "model": self.model, "messages": messages, "temperature": 0, "seed": 7,
            "response_format": {"type": "json_object"},
        }).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(f"{self.base_url}/chat/completions", data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            content = json.load(resp)["choices"][0]["message"]["content"]
        if self.cache:
            self.cache.put(key, content)
        return content


class FunctionBackend:
    """Wrap a Python function as a backend. Used by the tests."""

    def __init__(self, name: str, fn: Callable[[list[dict[str, str]]], str]):
        self.name, self.fn, self.calls = name, fn, 0

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls += 1
        return self.fn(messages)


def from_env(tier: str, cache: Cache | None = None) -> OpenAICompatible | None:
    """Build the "local" or "remote" backend from environment variables, if configured."""
    prefix = "LOCAL" if tier == "local" else "REMOTE"
    base_url, model = os.getenv(f"{prefix}_BASE_URL"), os.getenv(f"{prefix}_MODEL")
    if not base_url or not model:
        return None
    return OpenAICompatible(tier, base_url, model, os.getenv(f"{prefix}_API_KEY", ""), cache)
