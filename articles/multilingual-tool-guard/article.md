# Your AI Agent Understood the Request. Did It Send the Right Amount?

*Build a deterministic Python guard that checks every LLM tool call against what the user actually typed, in Sindhi, Urdu, Roman Urdu and English.*

By Faheem Khaskheli · November 17, 2026 · AI Agents / Multilingual NLP / Python

A Sindhi user types:

> منهنجي A-100 اڪائونٽ مان B-200 اڪائونٽ ۾ ۱۵۰۰ رپيا موڪليو.

"Send 1500 rupees from my account A-100 to account B-200." The model answers with a tool call. The JSON is valid, the function name is right, and the amount says `15000`.

Nothing in a normal agent stack stops that call. The schema check passes because `15000` is an integer. The model was not "confused" in any visible way. It simply produced the wrong argument, and the tool did exactly what it was told.

I built [Sindhi-AgentBench](https://github.com/faheemkhaskheli9/Sindhi-AgentBench) to measure whether tool-using agents can complete simulated banking, booking, shopping and government tasks in Sindhi, Roman Sindhi, Urdu and English. The benchmark scores what the agent **does**, not what it says. Building it made one thing clear: most of the dangerous failures are not wrong tools. They are wrong **arguments**.

Research points the same way. The [MLCL study (Lost in Execution, ACL 2026)](https://arxiv.org/abs/2601.05366) tested tool calling in Chinese, Hindi and Igbo and found that many failures happen even when the model understood the request: the parameter values break execution-level conventions. [MASSIVE-Agents](https://aclanthology.org/2025.findings-emnlp.1099.pdf) moved a function-calling benchmark to 52 languages and found large cross-lingual gaps in function-call correctness.

This article builds a small, deterministic **argument guard** that sits between the model and the tool. The [complete runnable project](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/multilingual-tool-guard) uses only the Python standard library, runs offline, and has a 54-test pytest suite.

**Scope:** the 28 tasks and all IDs are synthetic, written for this tutorial and not reviewed by native speakers. No real transactions happen anywhere.

## Why English-first guards fail on South Asian input

The common fix is "check that the amount appears in the user message". In English that is a regex. In Pakistan, the same number arrives in at least five forms:

1. Western digits: `1500`, `1,500`, or South Asian grouping `1,50,000`.
2. Extended Arabic-Indic digits: `۱۵۰۰`. Unicode lists [U+06F0 to U+06F9 as the digits used with Persian, Urdu and Sindhi](https://www.unicode.org/terminology/digits.html), separate from the Arabic-Indic digits at U+0660.
3. Number words in script: `پنج هزار` (Sindhi) or `پانچ ہزار` (Urdu), both "five thousand".
4. Number words in Roman script: `panj hazar`, `paanch hazar`, `pandrah sau` (fifteen hundred).
5. Indian-system units: `2.5 lakh` or `ٻه لک پنجاهه هزار` (two lakh fifty thousand), both 250,000.

Even the letters disagree. The Sindhi `ه` and the Urdu `ہ` in "hazar" are different code points, and so are the Sindhi `ڪ` and the Urdu `ک`. A string comparison sees different words.

The other problem is **direction**. A transfer has a source and a destination. Both account IDs appear in the message, so "is the ID in the text?" passes even when the model swaps them. In Urdu and Sindhi the role is carried by a postposition after the ID (`سے` / `مان` mean "from", `میں` / `۾` mean "in"), not by word order.

## The design: the model proposes, the guard decides

The guard returns one of three actions for every proposed call:

1. **block**: an argument is not supported by the user's words, has the wrong type, breaks a limit, or contradicts the grammar of the request.
2. **confirm**: the call is grounded but changes state, so the user sees the exact arguments in their own language and replies yes or no.
3. **execute**: the call is grounded and read-only.

The guard never repairs a call. If it fixed `15000` to `1500`, it would be making a decision the user never saw. A blocked call goes back to the model or to the user.

## Step 1: Normalize scripts before comparing anything

`normalize.py` turns text into a comparison form: NFKC, both Arabic digit ranges mapped to ASCII, letter variants unified, diacritics removed, casefolded.

```python
_DIGIT_MAP = {0x0660 + i: str(i) for i in range(10)} | {0x06F0 + i: str(i) for i in range(10)}

_LETTER_MAP = {
    "ك": "ک", "ڪ": "ک",            # Arabic kaf, Sindhi swash kaf -> Urdu kaf
    "ي": "ی", "ى": "ی",            # yeh variants
    "ہ": "ه", "ھ": "ه",            # Urdu heh forms -> one heh
    "ڙ": "ڑ",                      # Sindhi rreh -> Urdu rreh
    "٬": "", "٫": ".",             # Arabic thousands and decimal separators
    "ـ": "", "‌": "",    # tatweel, zero-width non-joiner
}
```

The lexicon of number words is passed through the same `normalize()` function at import time. That one decision means Sindhi `هزار` and Urdu `ہزار` become the same key without listing both.

One detail cost me a failed test: the Sindhi postposition `۾` (U+06FE, "in") is a Unicode **symbol**, not a letter. Python's `\w` does not match it, so a tokenizer built on `\w+` silently drops the most common Sindhi destination marker. The tokenizer adds it explicitly:

```python
return re.findall(r"\w+(?:-\w+)*|۾", normalize(text))
```

## Step 2: Extract every number the user could have meant

`extract_numbers()` returns a **set** of integers, not one answer. The guard only needs to know whether the model's value is one of them.

```python
>>> extract_numbers("منهنجي A-100 مان ۱۵۰۰ رپيا")
{1500}
>>> extract_numbers("ٻه لک پنجاهه هزار")
{250000}
>>> extract_numbers("one thousand five hundred and 2 seats")
{2, 1500}
```

Three rules keep the set honest:

1. **Identifiers are removed first.** `A-100` is an account, not an amount. Without this rule, a model that sends 100 rupees would be "grounded" by the account number.
2. **Compound phrases are summed while the multiplier falls.** "two lakh fifty thousand" becomes 250,000, and a new number starts when the multiplier rises again.
3. **Ambiguous Roman words count only before a multiplier.** `do` is "two" in Roman Urdu and also "do it" (`bill bhar do`). `no` is "nine" and also "no". Alone they are ignored; `do hazar` is 2,000.

## Step 3: Check identifiers and their roles

Every string argument declared as an identifier must appear as a token in the normalized request. Then, for arguments with a role, the guard looks at a two-token window around the ID:

```python
_SOURCE_AFTER = {"مان", "سے", "maan", "se", "say"}
_DEST_AFTER = {"۾", "ڏانهن", "کي", "میں", "کو", "mein", "ko"}
_SOURCE_BEFORE = {"from"}
_DEST_BEFORE = {"to", "into"}

def _role_of(value, toks):
    i = toks.index(value)
    after = set(toks[i + 1 : i + 3])
    before = set(toks[max(0, i - 2) : i])
    source = bool(after & _SOURCE_AFTER or before & _SOURCE_BEFORE)
    dest = bool(after & _DEST_AFTER or before & _DEST_BEFORE)
    if source == dest:
        return None   # no cue, or both cues: do not guess
    return "source" if source else "destination"
```

Urdu and Sindhi postpositions come after the ID; English prepositions come before it. The window of two allows "A-100 account se" and "from account A-100". When the cue is missing or contradictory, the guard does not invent a role. It returns `None` and the confirmation step carries the risk.

This is also why word order does not matter. In `B-200 کو A-100 سے پندرہ سو روپے دیں۔` the destination comes first, and the guard still reads it correctly.

## Step 4: Put it together in check_call

```python
def check_call(user_text, call, tools=TOOLS, config=FULL):
    spec = tools.get(call.get("name", ""))
    if spec is None:
        return Decision("block", [Issue("unknown_tool", None, call.get("name"))], lang)
    # 1. schema: missing and unexpected arguments
    # 2. numbers: integer type, positive, grounded in extract_numbers(), under max_value
    # 3. identifiers: grounded in tokens(), role matches the user's grammar
    if issues:
        return Decision("block", issues, lang)
    if spec.writes:
        return Decision("confirm", [], lang, confirmation_message(spec.name, args, lang))
    return Decision("execute", [], lang)
```

Note `type(value) is not int`, not `isinstance`. In Python `True` is an `int`, and a model that sends `"amount_pkr": true` should not transfer one rupee.

Run the demo:

```bash
cd examples/multilingual-tool-guard
python -m tool_guard demo
```

For the Sindhi request above, the correct call returns `confirm` with this message:

```text
تصديق ڪريو: A-100 مان B-200 ۾ 1,500 رپيا موڪلڻا آهن؟ ها يا نه؟
```

The extra-zero call is blocked with `ungrounded_number: 15000 not found; user wrote [1500]`. The swapped call is blocked twice: `user marked B-200 as destination` and `user marked A-100 as source`.

The confirmation echoes amounts with Western digits and a thousands separator. That is a deliberate choice: the user should compare exactly what will execute, and `1,500` against `15,000` is easier to see than the same values written as words.

## Step 5: Measure it with an ablation

The test set is 28 requests: 7 intents (transfers with digits, words, lakh and reversed word order, a bill payment, a bus booking and a balance check), each written in Sindhi, Urdu, Roman Sindhi/Urdu and English. For every correct call, `mutations.py` creates corrupted versions that a guard should stop: an extra zero, a lost zero, a misread leading digit, swapped accounts, a near-miss ID, the amount as a string, an invented argument and a dropped argument.

The evaluator runs four guard configurations. One rule matters: a guard that rejects the correct call "catches" every corruption for free, so corruptions are counted only on requests the guard can serve.

```bash
python -m tool_guard evaluate
```

Measured on the tutorial set:

1. **ASCII-only guard** (Western digits, no number words, no roles): allowed 12 of 28 correct calls (43%). Only 2 of 7 Sindhi and 2 of 7 Urdu requests could be served. On the requests it served, it caught 68 of 73 corruptions, but 0 of 5 swapped transfers.
2. **Plus script digits**: allowed 15 of 28 correct calls (54%). Swaps caught: 0 of 6.
3. **Plus number words and lakh**: allowed 28 of 28 correct calls. Caught 180 of 196 corruptions (92%). Swaps caught: 0 of 16.
4. **Full guard, plus role cues**: allowed 28 of 28 correct calls and blocked 196 of 196 corruptions, including 16 of 16 swaps.

The first line is the real lesson. An English-first guard does not fail open on Sindhi and Urdu; it fails **closed**, rejecting most correct requests. In production that means someone eventually loosens or removes it, and then nothing checks the arguments at all.

The last line is not a quality claim. I wrote the rules and the 28 tasks together, so a perfect score only shows that the code does what this article describes. It says nothing about real user text. That is what the next section is for.

## The failures I kept on purpose

`data/limitations.jsonl` records cases where the guard is wrong, and `tests/test_limitations.py` asserts that it stays wrong in exactly the documented way. If someone fixes one, the test fails and the documentation must change with it.

```bash
python -m tool_guard limitations
```

1. **Fraction words.** Sindhi `ڏيڍ هزار` (one and a half thousand) and Urdu `سوا لاکھ` (one and a quarter lakh) are not in the lexicon. Correct calls are blocked.
2. **Self-correction.** "1500 bhejo, nahi nahi 2000 bhejo" contains both numbers. A call with 1500 is grounded and goes to confirmation. The guard checks that a value was said, not that it was the final intent.
3. **No role cue.** "Accounts A-100 and B-200: move 1500, the second one pays" has no from/to marker. A swapped call is not detected.
4. **Roman Urdu "to".** In "Pehle balance dekho, to A-100 ka 1500 B-200 mein bhejo", `to` means "then". The English cue list reads it as "to A-100" and blocks a correct call.

Cases 2 and 3 are why every state-changing tool still asks for confirmation. Grounding narrows the space of wrong calls. It does not prove the right one.

## Connect a real model

The optional `ask` command sends the request to any OpenAI-compatible Chat Completions server with the tool schemas, then guards whatever the model returns.

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_BASE_URL`, `OPENAI_API_KEY` and `LLM_MODEL`. For a local model, use Ollama at `http://localhost:11434/v1` and leave the key empty.
3. Run `python -m tool_guard ask "C-310 se D-420 ko paanch hazar rupay bhejo."`

The schemas declare `amount_pkr` and `seats` as integers with `additionalProperties: false`. Strict schemas reduce type errors. They cannot tell 1500 from 15000.

## Expert notes before you ship this

1. **Keep the guard outside the model.** If the same model that produced the call also judges it, both steps share the same misreading. The guard here is plain code with no model call.
2. **Prefer block plus ask over silent repair.** Auto-correcting an amount is a new decision the user never approved.
3. **Lexicons are data, not code.** Dialects and spellings vary across Sindh and Punjab. Store the word lists in reviewed files and grow them from blocked real requests, with native-speaker review.
4. **Log blocks by language.** A block rate that is much higher for Sindhi than English is a coverage bug in the guard, not a user problem.
5. **Limits belong in the tool spec.** `max_value` catches grounded but dangerous values. A user can really type 20 seats; the business rule decides whether that is allowed.
6. **Confirmation must show the arguments, not the model's summary.** The message is rendered from the call itself, so it cannot hide a wrong value behind friendly wording.

## Run it yourself

```bash
git clone https://github.com/faheemkhaskheli9/Articles.git
cd Articles/examples/multilingual-tool-guard
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q
python -m tool_guard demo
python -m tool_guard evaluate
```

VS Code launch configurations for the demo, the evaluation, the limitations, the LLM command and pytest are in `.vscode/launch.json`.

## References

1. Luo et al., [Lost in Execution: On the Multilingual Robustness of Tool Calling in Large Language Models](https://arxiv.org/abs/2601.05366), ACL 2026.
2. [MASSIVE-Agents: A Benchmark for Multilingual Function-Calling in 52 Languages](https://aclanthology.org/2025.findings-emnlp.1099.pdf), Findings of EMNLP 2025.
3. Unicode Consortium, [Terminology for Digits](https://www.unicode.org/terminology/digits.html).
4. [Sindhi-AgentBench](https://github.com/faheemkhaskheli9/Sindhi-AgentBench), my offline harness for Sindhi, Roman Sindhi, Urdu and English tool-using agents.
5. [Companion code for this article](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/multilingual-tool-guard).
