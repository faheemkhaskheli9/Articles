# Most of Your LLM Calls Don't Need an LLM

*Build a cascade that tries plain rules first, a local model second and a paid model last, and checks every answer before it trusts it. Standard-library Python, offline tests, and numbers from a held-out set, including the errors.*

By Faheem Khaskheli · November 17, 2026 · LLM Applications / Cost / Python

Here is a job posting:

> LLM Engineer, Berlin. This is not a remote position; you will join the team in our Kreuzberg office. EU Blue Card support is provided.

I want three facts from it: does the company sponsor visas, is the job remote, hybrid or on-site, and is German required. A paid LLM answers this well. It also costs money on every call, takes seconds, and can give a different answer tomorrow.

Two of the three answers are sitting in plain sight. "Not a remote position" means on-site. "Blue Card support is provided" means sponsorship. A regular expression gets both in microseconds. Only the third field (German) is not mentioned, and even that can be answered without a model if you trust that "not mentioned" means "not required".

I keep a repository called [Local-AI-Ops](https://github.com/faheemkhaskheli9/Local-AI-Ops) with one rule in its README: if you asked an LLM to do the same mechanical thing twice, turn it into a function. Its job pipeline filters postings for visa and language requirements before any model sees them. This article turns that rule into a reusable pattern: a **cascade** where each tier handles what it can and passes only the rest upward.

The [complete runnable project](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/llm-cascade) uses only the Python standard library, runs offline, and has a 42-test pytest suite.

**Scope:** all 48 job postings are synthetic and written for this tutorial. The model tiers are tested with fake backends; this article reports no real model accuracy. Run `evaluate --local` with your own model to measure that.

## The idea is not new, and it works

Chen, Zaharia and Zou describe the **LLM cascade** in FrugalGPT: send a query to a cheap model first and escalate to an expensive one only when the cheap answer is not good enough. On their benchmarks, the cascade matched the best single model with up to 98% lower cost ([arXiv 2305.05176](https://arxiv.org/abs/2305.05176)). RouteLLM trains a router that decides up front which of two models to call and reports over 2x cost savings without losing quality ([ICLR 2025, arXiv 2406.18665](https://arxiv.org/abs/2406.18665)).

Both papers start the cascade at a model. For extraction work the cheapest tier is not a model at all. It is code.

The hard part of any cascade is not the tiers. It is the question at each step: **is this answer good enough to stop here?** FrugalGPT trains a scorer for that. In extraction we can do something simpler and stricter: check the answer against the source text.

## When to use this pattern

Use it when:

- the same kind of request arrives many times (postings, tickets, invoices, emails)
- the answer has a fixed shape: a small set of allowed values, plus a quote you can verify
- a large share of inputs use predictable wording
- a wrong answer costs more than an extra model call

Do not use it for open-ended writing or reasoning, where there is no cheap way to check the answer.

## The design

The whole system fits in five files:

1. `rules.py` answers a field only when every clause that mentions it agrees, and abstains otherwise.
2. `compact.py` builds the prompt from only the clauses that mention the open fields.
3. `validate.py` checks each model answer: allowed value, a real quote, and no contradiction with the rules.
4. `backends.py` talks to any OpenAI-compatible endpoint and caches answers in SQLite.
5. `cascade.py` runs rules, then each model in order, passing only the fields still open.

A field that fails every tier comes back as `needs_review`. The system never invents an answer to fill the gap.

## Step 1: rules that know when to stay quiet

A rule that guesses is worse than no rule. So the rules tier has three possible outcomes per field: a value, the default value when the topic is not mentioned at all, or `None`, which means "escalate".

First split the posting into clauses, then classify each clause that mentions the field:

```python
_VISA_TERM = r"(?:visas?|sponsor\w*|blue card)"
_VISA_NO = [
    re.compile(r"\b(?:no|not|cannot|can't|can not|unable to|do not|don't|won't|without)\b"
               r"(?:\W+\w+){0,6}?\W+" + _VISA_TERM, re.I),
    re.compile(_VISA_TERM + r"(?:\W+\w+){0,3}?\W+(?:none|not available|not provided|not offered)\b", re.I),
    re.compile(r"\bmust\b.{0,40}\b(?:right to work|authori[sz]ed to work|work permit)\b", re.I),
]
_VISA_YES = re.compile(
    r"\b(?:offer|offers|provide|provided|provides|available|support|assistance|included|yes|we sponsor)\b", re.I)


def classify(field: str, clause: str) -> str | None:
    if field == "visa_sponsorship":
        if any(p.search(clause) for p in _VISA_NO):
            return "no"
        if re.search(_VISA_TERM, clause, re.I) and _VISA_YES.search(clause):
            return "yes"
        return None
    ...
```

The negative patterns run first. "We do not provide visa sponsorship" contains "provide", and checking for "yes" first would get it backwards.

Then decide per field:

```python
def extract_field(field, text, trust_absence=True):
    relevant = [c for c in clauses(text) if mentions(field, c)]
    if not relevant:
        return FieldResult(DEFAULT_WHEN_ABSENT[field], "", "rules") if trust_absence else None
    answers, strong_unclear = {}, False
    for clause in relevant:
        value = classify(field, clause)
        if value is not None:
            answers.setdefault(value, clause)
        elif mentions(field, clause, strong_cues(field)):
            strong_unclear = True
    if len(answers) == 1 and not strong_unclear:
        value, clause = next(iter(answers.items()))
        return FieldResult(value, clause, "rules")
    return None  # conflicting, unclear or only weak signals: escalate
```

Two details matter here.

**Weak cues.** "Snacks and good coffee are available in every office" mentions an office but says nothing about the work mode. The word "office" is a weak cue: a weak-cue clause the rules cannot read does not block a clear answer from another clause. A clause with a strong cue, such as "Office-first culture with optional remote Fridays", does block it, because "remote" is in it and the rules cannot tell what it means.

**Abstain on conflict.** If one clause says "yes" and another says "no", the rules do not pick a winner. They escalate.

Here is the rules tier on the posting from the start (`python -m llm_cascade demo`):

```text
visa_sponsorship  yes          [rules] EU Blue Card support is provided.
work_mode         onsite       [rules] This is not a remote position;
german            -> next tier (rules abstained)
```

German escalated because this posting ends with a company blurb: "We are proud to be a German-founded company". The word "German" is there, no pattern explains it, so the rules step aside instead of guessing.

## Step 2: send the model less

When a field escalates, the model does not need the whole posting. It needs the clauses that talk about that field:

```python
def compact_context(text, fields, max_chars=1200):
    seen, kept = set(), []
    for clause in clauses(text):
        key = clause.lower()
        if key in seen:
            continue
        if any(mentions(f, clause) for f in fields):
            seen.add(key)
            kept.append(clause)
    context = " ".join(kept) if kept else text
    return context[:max_chars]
```

The prompt lists only the open fields and their allowed values, and asks for an exact quote as evidence:

```python
SYSTEM_PROMPT = (
    "You extract facts from job postings. Answer only from the text. "
    "Return JSON: an object whose keys are the requested field names; each value is "
    '{"value": <one allowed value>, "evidence": <exact quote copied from the text, or "" if the text says nothing>}.'
)
```

If nothing matches, the full text is sent. That happens when a field escalates because no cue word was found at all (Step 5 explains why you might want that).

## Step 3: check the answer before you trust it

This is the step that makes a cascade safe. A cheap model that answers confidently and wrongly saves no money; it moves the cost into your bug tracker.

```python
def check_answer(field, answer, posting):
    if not isinstance(answer, dict):
        return False, "answer is not an object"
    value, evidence = answer.get("value"), answer.get("evidence", "")
    if value not in FIELDS[field]:
        return False, f"value {value!r} is not allowed"
    if not isinstance(evidence, str):
        return False, "evidence is not a string"
    if not evidence.strip():
        if value == DEFAULT_WHEN_ABSENT[field]:
            return True, "no evidence needed for the default value"
        return False, "non-default value without evidence"
    if _norm(evidence) not in _norm(posting):
        return False, "evidence is not a quote from the posting"
    for clause in clauses(evidence):
        if mentions(field, clause):
            ruled = classify(field, clause)
            if ruled is not None and ruled != value:
                return False, f"rules read the evidence as {ruled!r}, model said {value!r}"
    return True, "ok"
```

Four checks, all deterministic:

1. The value is one of the allowed values.
2. A non-default value comes with evidence.
3. The evidence is a real quote from the posting, after whitespace and case are normalised. This catches invented quotes.
4. The rules do not read the quoted text the other way. If the model says "yes" and quotes "We do not sponsor visas", the answer is rejected.

The rules now play two roles. They answer the easy cases, and they act as a cross-check on the hard ones.

## Step 4: run the tiers

```python
class Cascade:
    def run(self, posting):
        found = extract(posting, self.fields, self.trust_absence)
        results = {f: r for f, r in found.items() if r is not None}
        outcome = Outcome(results)
        pending = [f for f in self.fields if f not in results]
        for backend in self.backends:
            if not pending:
                break
            context = compact_context(posting, pending) if self.compact else posting
            messages = build_messages(context, pending)
            try:
                payload = json.loads(backend.complete(messages))
            except (json.JSONDecodeError, OSError, KeyError, IndexError, ValueError) as exc:
                ...  # record the failure; every pending field moves up one tier
                continue
            for f in pending:
                ok, reason = check_answer(f, payload.get(f), posting)
                if ok:
                    results[f] = FieldResult(payload[f]["value"], payload[f].get("evidence", ""), backend.name)
            pending = [f for f in pending if f not in results]
        for f in pending:
            results[f] = FieldResult("needs_review", "", "review")
        ...
```

Each tier sees fewer fields than the one before. If the local model answers German correctly but invents a quote for work mode, only work mode goes to the paid model. A broken JSON reply or a refused connection is treated the same as a wrong answer: the fields move up.

The backend is one small class for any OpenAI-compatible server, so the local tier can be [Ollama](https://ollama.com/blog/openai-compatibility) and the paid tier any hosted API. Requests use `temperature=0` and a fixed `seed`, and every answer is cached in SQLite by a hash of model, URL and messages. A posting you have already processed costs nothing the second time. Note that a seed makes output repeatable only as far as the server supports it; OpenAI documents it as best effort. The cache is what makes reruns truly identical.

## Step 5: measure, including a held-out set

The repository has two datasets:

- `postings.jsonl`: 32 postings. I wrote the rules while looking at these.
- `holdout.jsonl`: 16 postings written after the rules were frozen. I did not change the rules after seeing these results.

The second set matters. Rules written against a dataset will always look perfect on that dataset.

Results from `python -m llm_cascade evaluate`, rules tier only, offline:

- Development set: the rules answered 80 of 96 fields (83%) with 0 errors. 14 of 32 postings needed a model call at all.
- Held-out set: the rules answered 30 of 48 fields (62%) with **4 errors**. 14 of 16 postings needed a model call.

Coverage dropped from 83% to 62% on text the rules had never seen. That drop is expected and is fine: an abstention costs one model call, nothing more.

The 4 errors are the interesting part. All four came from the same place, and it was not the patterns:

```text
hold-04.visa_sponsorship: rules=unknown label=no
hold-05.visa_sponsorship: rules=unknown label=yes
hold-05.work_mode: rules=unknown label=onsite
hold-12.work_mode: rules=unknown label=onsite
```

Every one is the **"not mentioned" default**. The postings said "Applicants must hold a valid EU work authorization", "We support Red-White-Red Card applications", "Daily presence at the plant is required" and "On site in Paris". None of those contain a word from the cue lists ("authorization" is not "authorized to work", "On site" is not "on-site"). The rules concluded the topic was absent and answered with the default.

This is the lesson I did not expect: **in a rules tier, the most dangerous rule is the one that detects absence.** A pattern that fails to match abstains, which is safe. An absence check that fails to see the topic answers, confidently and wrongly.

So the cascade has a switch, `trust_absence`. With `trust_absence=False`, "no cue word found" also escalates:

- Held-out set: the rules answered 16 of 48 fields (33%) with 0 errors. 15 of 16 postings needed a model call.
- Development set: 61 of 96 fields (64%), 0 errors, 26 of 32 postings needed a model call.

You trade coverage for safety. Which side you pick depends on what a wrong "unknown" costs you. For a job filter that hides postings, a wrong "no sponsorship" costs a missed job, so I would distrust absence.

### What reaches the model

Token counts here are estimates (about 4 characters per token), used only to compare prompts built from the same text. Use your provider's tokenizer for billing.

- Development set, sending every posting with all three fields to a model: about 7,548 prompt tokens.
- Sending only escalated postings, full text, only open fields: about 2,980.
- Sending only escalated postings, compacted: about 1,540, which is **20%** of sending everything.
- Held-out set, same comparison: about 1,433 against 2,382, or **60%**, because the rules answered less.
- With `trust_absence=False`, the development set goes up to about 4,019 tokens (53%).

The saving comes from two separate places: fewer calls (rules answer whole postings) and smaller calls (compaction removes company blurbs and benefits lists). On the held-out set the saving is smaller, and that is the honest number to plan with.

## Step 6: test the failure paths, not just the happy path

The test suite spends most of its effort on what happens when a tier misbehaves. Some examples from `tests/test_cascade.py`:

```python
def test_invented_evidence_escalates_to_the_next_tier():
    local = FunctionBackend("local", answer(
        work_mode={"value": "remote", "evidence": "This role is fully remote."},  # not in the text
        german={"value": "not_required", "evidence": ""},
    ))
    remote = FunctionBackend("remote", answer(
        work_mode={"value": "hybrid", "evidence": "optional remote Fridays"},
    ))
    out = Cascade([local, remote]).run(POSTING)
    assert out.results["german"].tier == "local"
    assert out.results["work_mode"].tier == "remote"
    assert "not a quote" in out.calls[0].rejected["work_mode"]
    assert out.calls[1].fields == ["work_mode"]


def test_broken_json_and_errors_fall_through_to_review():
    broken = FunctionBackend("local", lambda m: "Sure! Here is the JSON:")

    def boom(messages):
        raise OSError("connection refused")

    out = Cascade([broken, FunctionBackend("remote", boom)]).run(POSTING)
    assert out.needs_review == ["work_mode", "german"]
```

Other tests cover: rules answering with zero model calls, only open fields reaching the model, a quote the rules contradict, compaction shrinking the prompt, the real HTTP client against a local fake server (checking `temperature=0`, `seed=7` and that the second run comes from the cache), and a test that pins every number quoted in this article. If the rules change, that test fails and the article must be updated with it.

## Adversarial cases worth keeping in your test set

These are the phrasings that broke or nearly broke my rules:

- "We do not provide visa sponsorship": a positive word inside a negative sentence.
- "German language skills are an advantage but not required": both "preferred" and "not required" in one clause.
- "French required, German a plus": "required" belongs to French. Splitting clauses on commas fixes it.
- "Relocation support is available": relocation is not sponsorship. The rules must abstain, not answer "yes".
- "Snacks are available in every office" in a fully remote job: boilerplate that mentions an office.
- "We are proud to be a German-founded company": the field's keyword in an unrelated sentence.
- "Applicants must hold a valid EU work authorization": the topic is present, but no cue word matches.

## Expert considerations

**The cue list is a model too.** It is small, readable and testable, but it has a vocabulary and it will miss words. Grow it from real escalations: every field the model answered that the rules abstained on is a candidate for a new pattern, and every `needs_review` is a candidate for a test.

**Abstention rate is a metric.** Track the share of fields each tier answers, per week. A sudden rise in escalations usually means the input changed (a new job board, a new language), not that the model got worse.

**Validation must be cheaper than the model.** Every check here is a string operation. If your check needs another LLM call, you have built a second model tier, not a validator.

**Determinism comes from the cache.** Temperature 0 and a seed reduce variation but do not remove it on every server. If you need the same answer for the same input, cache it.

**Language matters.** The rules here are English. In the held-out set, "Deutsch fliessend erforderlich" is noticed only because "Deutsch" is a cue word; no English pattern can read it, so the field escalates. For multilingual input, add patterns per language or let those fields escalate.

## Limitations

- The datasets are small (48 postings) and synthetic. They show how the design behaves, not how well it works on real job boards.
- No real model was run for this article. The model tiers are tested with fakes; their accuracy depends on your model.
- Token counts are estimates.
- Clause splitting on commas helps with lists but can split a sentence that needs to stay together.
- Evidence checking proves a quote exists, not that the quote supports the value. The rules cross-check catches some contradictions, not all.

## Run it

```bash
git clone https://github.com/faheemkhaskheli9/Articles.git
cd Articles/examples/llm-cascade
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest -q
python -m llm_cascade demo
python -m llm_cascade evaluate
```

To add a local model, install [Ollama](https://ollama.com/download), run `ollama pull qwen2.5:7b`, copy `.env.example` to `.env`, and run `python -m llm_cascade evaluate --local`. Add a paid key to `.env` and use `--local --remote` for the full cascade.

## Takeaways

1. Put plain code in front of your model and let it answer only when it is sure.
2. Make every tier able to say "I don't know", and treat that as a normal outcome.
3. Check each model answer against the source before you accept it; a failed check is a reason to escalate, not a reason to retry the same model.
4. Be most suspicious of rules that detect absence.
5. Measure on text your rules have never seen.

## References

- Lingjiao Chen, Matei Zaharia, James Zou. [FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance](https://arxiv.org/abs/2305.05176). arXiv 2305.05176, 2023.
- Isaac Ong et al. [RouteLLM: Learning to Route LLMs with Preference Data](https://arxiv.org/abs/2406.18665). ICLR 2025.
- Ollama. [OpenAI compatibility](https://ollama.com/blog/openai-compatibility).
- OpenAI. [Chat Completions API reference](https://platform.openai.com/docs/api-reference/chat/create) (the `seed` parameter).
- Faheem Khaskheli. [Local-AI-Ops](https://github.com/faheemkhaskheli9/Local-AI-Ops): toolkit for moving repeatable LLM work to local models and Python.
- Companion code: [examples/llm-cascade](../../examples/llm-cascade/README.md).
