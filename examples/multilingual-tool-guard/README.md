# Multilingual tool-call argument guard

Companion code for [Your AI Agent Understood the Request. Did It Send the Right Amount?](../../articles/multilingual-tool-guard/article.md)

A deterministic guard that sits between an LLM and its tools. It checks every proposed call against
the words the user typed in **Sindhi, Urdu, Roman Sindhi/Urdu or English** and returns `block`,
`confirm` or `execute`.

- Reads Western digits, Arabic-Indic and Extended Arabic-Indic digits (`۱۵۰۰`), South Asian grouping (`1,50,000`).
- Reads number words and lakh/crore: `پنج هزار`, `پانچ ہزار`, `paanch hazar`, `ٻه لک پنجاهه هزار`, `2.5 lakh`.
- Unifies letter variants (`ڪ`/`ک`, `ه`/`ہ`, `ڙ`/`ڑ`) before comparing.
- Checks from/to roles with postposition and preposition cues (`مان`, `سے`, `۾`, `میں`, `se`, `from`, `to`).
- Asks for confirmation of every state-changing call, in the user's language.

Standard library only. Runs offline. The optional `ask` command calls an OpenAI-compatible model.

## Setup (step by step)

1. Install Python 3.11 or newer.
2. Open a terminal in this folder:
   ```bash
   cd examples/multilingual-tool-guard
   ```
3. Install the test runner and the package:
   ```bash
   python -m pip install -r requirements.txt
   python -m pip install -e .
   ```
4. Run the tests:
   ```bash
   python -m pytest -q
   ```

## Commands

```bash
python -m tool_guard demo          # one Sindhi request, three proposed calls
python -m tool_guard evaluate      # ablation over data/tasks.jsonl
python -m tool_guard limitations   # known failure cases, kept on purpose
python -m tool_guard check "C-310 se D-420 ko paanch hazar rupay bhejo." '{"name": "bank.transfer", "arguments": {"from_account": "C-310", "to_account": "D-420", "amount_pkr": 5000}}'
```

## Use a real model (optional)

1. Copy `.env.example` to `.env`.
2. Fill in `OPENAI_BASE_URL`, `OPENAI_API_KEY` and `LLM_MODEL`. For Ollama use `http://localhost:11434/v1` and leave the key empty.
3. Run:
   ```bash
   python -m tool_guard ask "C-310 se D-420 ko paanch hazar rupay bhejo."
   ```

## VS Code

Open the `Articles` repository root or this folder. The Run and Debug panel lists
`Tool Guard: Demo`, `Evaluate ablation`, `Known limitations`, `Check one Urdu call`, `Ask LLM` and `pytest`.

## Files

- `src/tool_guard/normalize.py`: script normalization, number extraction, tokens.
- `src/tool_guard/guard.py`: tool specs, role cues, `check_call`, confirmation messages.
- `src/tool_guard/mutations.py`: deterministic corruptions of correct calls.
- `src/tool_guard/evaluate.py`: four-configuration ablation.
- `src/tool_guard/llm.py`: optional OpenAI-compatible tool-calling client.
- `data/tasks.jsonl`: 28 synthetic requests (7 intents x 4 languages).
- `data/limitations.jsonl`: documented failures, asserted by `tests/test_limitations.py`.

## Limits

The tasks are synthetic and not reviewed by native speakers. The rules and tasks were written
together, so the full guard's perfect score on them is not evidence of real-world accuracy.
Fraction words (`ڏيڍ`, `سوا`), self-corrections and requests without role cues are not handled;
see `python -m tool_guard limitations`. No real transactions are performed.
