# Verifiable Legal RAG: Runnable Companion

Companion code for the article [Your Legal AI Cited Section 4. Did Section 4 Actually Say That?](../../articles/verifiable-legal-rag/article.md), based on the approach in [pakistani-lawyer-ai](https://github.com/faheemkhaskheli9/pakistani-lawyer-ai).

The pipeline chunks statutes by provision, retrieves with BM25, abstains when evidence is weak, requires every generated claim to carry a citation and a verbatim quote, and verifies both before showing an answer.

**The corpus is original fictional text.** It is not Pakistani law and nothing here is legal advice. The Urdu/Roman Urdu glossary and the evaluation questions are small, hand-written and synthetic.

## Requirements

- Python 3.11 or newer
- No runtime dependencies (standard library only); `pytest` for tests
- No API key or network for the default extractive generator

## Setup

1. Clone and enter the folder:
   `git clone https://github.com/faheemkhaskheli9/Articles.git` then `cd Articles/examples/verifiable-legal-rag`
2. Create a virtual environment: `python -m venv .venv`
3. Activate it: `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows)
4. Install: `python -m pip install -r requirements.txt` then `python -m pip install -e .`
5. Test: `python -m pytest -q`

## Commands

| Command | What it does |
|---|---|
| `python -m legal_rag ask "QUESTION"` | Answer with verified citations, or abstain |
| `python -m legal_rag ask --json "QUESTION"` | Full trace: retrieval scores, coverage, claims, rejected issues |
| `python -m legal_rag search "QUERY"` | Retrieval and gate decision only |
| `python -m legal_rag evaluate` | 19 synthetic questions, outcomes by language |
| `python -m legal_rag sweep` | Coverage threshold vs. unsafe answers and misses |
| `python -m legal_rag verify-fixtures` | Verifier against 11 adversarial model drafts |

Global options go before the command, for example `python -m legal_rag --min-coverage 0.35 evaluate`.

## Optional: use an LLM

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_BASE_URL`, `OPENAI_API_KEY` and `LLM_MODEL`. For Ollama use `http://localhost:11434/v1` and leave the key empty.
3. Run `python -m legal_rag --generator openai ask --json "Can a landlord cut off electricity to make a tenant leave?"`

Model output that fails verification is never shown; the pipeline falls back to a verified extractive answer or abstains. Real API calls may cost money. Tests never call a real model.

## VS Code

Open this folder (or the repository root) in VS Code, select the Python 3.11+ interpreter from `.venv`, and use the Run and Debug profiles in `.vscode/launch.json`: ask (English, Urdu, LLM), evaluate, threshold sweep, verify fixtures and pytest.

## Project layout

```text
data/corpus/          fictional statute text, one Section/Rule per chunk
data/glossary.json    tiny Urdu/Roman Urdu -> English term map (demo only)
data/eval/            questions.jsonl, adversarial_drafts.jsonl
src/legal_rag/
  corpus.py           provision-level chunking with stable IDs
  retrieval.py        BM25, query expansion, abstention gate
  generation.py       claim/citation/quote contract, extractive + OpenAI-compatible generators
  verify.py           deterministic citation checks
  pipeline.py         gate -> generate -> verify -> fallback/abstain
  evaluate.py         outcome classification and verifier fixtures
  cli.py              command line
tests/                pytest suite, including Medium HTML structure checks
```

## Limits

Verification proves that quoted words exist in the cited, retrieved provision. It does not prove the claim follows from them, applies to a user's facts, or reflects current law. The negation heuristic deliberately rejects some correct paraphrases. The evaluation numbers measure this fixture set only.
