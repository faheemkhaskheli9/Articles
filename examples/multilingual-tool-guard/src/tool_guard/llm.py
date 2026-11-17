"""Optional: let an OpenAI-compatible model propose the tool call, then guard it.

Works with OpenAI or a local Ollama server (http://localhost:11434/v1). Standard library only.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

from tool_guard.guard import TOOLS, ToolSpec

SYSTEM = (
    "You turn banking, bill and bus requests written in Sindhi, Urdu, Roman Sindhi/Urdu or English "
    "into exactly one tool call. Copy IDs exactly. Amounts and seat counts are integers."
)


def load_env(path: Path = Path(".env")) -> None:
    """Minimal .env reader so the example needs no extra package. Existing variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def tool_schemas(tools: dict[str, ToolSpec] = TOOLS) -> list[dict[str, Any]]:
    schemas = []
    for spec in tools.values():
        props: dict[str, Any] = {n: {"type": "integer"} for n in spec.numbers}
        props |= {n: {"type": "string"} for n in spec.identifiers}
        schemas.append({
            "type": "function",
            "function": {
                # Some providers reject dots in function names.
                "name": spec.name.replace(".", "_"),
                "parameters": {"type": "object", "properties": props, "required": sorted(props),
                               "additionalProperties": False},
            },
        })
    return schemas


def parse_tool_call(response: dict[str, Any]) -> dict[str, Any] | None:
    """Extract {"name", "arguments"} from a Chat Completions response, or None."""
    message = response["choices"][0]["message"]
    calls = message.get("tool_calls") or []
    if not calls:
        return None
    fn = calls[0]["function"]
    names = {spec.name.replace(".", "_"): spec.name for spec in TOOLS.values()}
    args = fn.get("arguments") or "{}"
    return {"name": names.get(fn["name"], fn["name"]),
            "arguments": json.loads(args) if isinstance(args, str) else args}


def propose_call(user_text: str) -> dict[str, Any] | None:
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("LLM_MODEL")
    if not model:
        raise SystemExit("Set LLM_MODEL in .env (see .env.example).")
    body = {
        "model": model,
        "temperature": 0,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_text}],
        "tools": tool_schemas(),
        "tool_choice": "required",
    }
    request = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', '')}"},
    )
    with urllib.request.urlopen(request, timeout=60) as resp:  # noqa: S310 - user-configured URL
        return parse_tool_call(json.load(resp))
