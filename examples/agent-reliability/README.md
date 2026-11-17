# AI Agent Reliability — Runnable Offline Companion

This is a standalone, **offline educational analogue** of a few research-evaluation patterns explored in [Sindhi-AgentBench](https://github.com/faheemkhaskheli9/Sindhi-AgentBench). It is not a copy of that research benchmark, and it does not test any live LLM by default.

## Install (Python 3.11+)

```bash
cd examples/agent-reliability
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Create `.env` from `.env.example` if desired; **no API key or network access is required** to run the demo.

## Run / test

```bash
python -m agent_reliability --json
python -m pytest -q
ruff check .
python tools/build_html.py --check
```

The demo deliberately constructs a false claim about an application status, then shows why a nonempty final answer can earn automatic completion credit even though an independent review rejects it. It also tests duplicate reservations, authorization, strict argument types, and a malicious note returned by a fictional government service.

This is **not** a real-model result or a production payment/booking simulator. The human review record is constructed for the demonstration; operational deployment would require independent annotators and audited controls.

## Files

- `src/agent_reliability/` — typed tools, deterministic mock environment, scoring code, synthetic four-language fixtures, CLI.
- `tests/` — safety, scoring, CLI, and Medium HTML tests.
- `tools/build_html.py` — regenerate `articles/the-tool-call-was-correct-the-ai-agent-was-still-wrong/index.html` from `source.md`.
- `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.env.example` — reproducible setup.
- Repository root `.vscode/launch.json` — debug profiles, including the offline demo and tests.

## Publishing

The Medium-importable article is at [`../../articles/the-tool-call-was-correct-the-ai-agent-was-still-wrong/index.html`](../../articles/the-tool-call-was-correct-the-ai-agent-was-still-wrong/index.html). Import the **GitHub Pages URL**, not a GitHub source file URL. See the repository root README. Medium's importer can still alter `<pre><code>` blocks, so check the preview on Android.
