# LLM cascade: rules first, local model second, paid model last

Companion code for the article [Most of Your LLM Calls Don't Need an LLM](../../articles/llm-cascade/article.md).

The task: read a job posting and extract three fields (visa sponsorship, work mode, German requirement), each with an exact quote as evidence.

1. **Rules** answer a field only when every relevant clause agrees. Otherwise they abstain.
2. **A local model** (any OpenAI-compatible server, for example Ollama) gets only the fields the rules left open, and only the clauses that mention them.
3. **A paid model** gets only the fields the local model failed on.
4. Every model answer is **checked** before it is accepted: allowed value, the quote really is in the posting, and the rules do not read the quote the other way. A failed check sends the field up one tier. A field that fails every tier is marked `needs_review`.

Runtime: Python 3.11+ standard library only. Model answers are cached in SQLite and requested with `temperature=0` and a fixed `seed`.

## Setup (step by step)

1. Get the code:
   ```bash
   git clone https://github.com/faheemkhaskheli9/Articles.git
   cd Articles/examples/llm-cascade
   ```
2. Create a virtual environment and install:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```
3. Run the tests: `pytest -q`
4. Run offline (no model needed):
   ```bash
   python -m llm_cascade demo
   python -m llm_cascade evaluate
   ```
5. Optional, local model tier: install [Ollama](https://ollama.com/download), then:
   ```bash
   ollama pull qwen2.5:7b
   cp .env.example .env              # LOCAL_* already points at Ollama
   python -m llm_cascade evaluate --local
   ```
6. Optional, paid tier: put `REMOTE_API_KEY` in `.env`, then `python -m llm_cascade evaluate --local --remote`.

Extract one posting:

```bash
python -m llm_cascade extract --text "Hybrid role in Berlin. We sponsor visas. German is a plus."
python -m llm_cascade extract --file posting.txt --local --remote --escalate-absent
```

VS Code: open this folder and use the launch configurations in `.vscode/launch.json` (also in the repository's root `.vscode/launch.json`).

## Data

- `data/postings.jsonl`: 32 synthetic postings. The rules were written while looking at these, so results on this set are optimistic.
- `data/holdout.jsonl`: 16 synthetic postings written after the rules were frozen. The rules were not changed after seeing their results.

Both sets are small and synthetic, written for this tutorial. They show the behaviour of the design, not a benchmark.

## Results (rules tier, offline, `python -m llm_cascade evaluate`)

| set | trust "not mentioned" | rules answered | rules wrong | postings needing a model |
|---|---|---|---|---|
| postings | yes | 80/96 | 0 | 14/32 |
| postings | no | 61/96 | 0 | 26/32 |
| holdout | yes | 30/48 | 4 | 14/16 |
| holdout | no | 16/48 | 0 | 15/16 |

All four holdout errors are the default answer for "topic not mentioned": the posting used words the cue list does not know ("work authorization", "Red-White-Red Card", "On site in Paris", "daily presence at the plant"). The patterns themselves made no errors. `--escalate-absent` (`trust_absence=False`) removes those errors and sends more fields to a model.

Token figures are estimates (characters / 4) used to compare prompts built from the same text; use your provider's tokenizer for billing.

The model tiers are tested with in-process fake backends and a local fake HTTP server. No real model accuracy is reported here; run `evaluate --local` to measure your own model.

## Files

| file | role |
|---|---|
| `src/llm_cascade/rules.py` | tier 1: clause patterns that abstain on conflict |
| `src/llm_cascade/compact.py` | prompt builder, clause-level context compaction, token estimate |
| `src/llm_cascade/validate.py` | checks a model answer before it is accepted |
| `src/llm_cascade/backends.py` | OpenAI-compatible client and SQLite cache |
| `src/llm_cascade/cascade.py` | runs the tiers and records every call |
| `src/llm_cascade/evaluate.py` | coverage, errors and token cost on both datasets |
