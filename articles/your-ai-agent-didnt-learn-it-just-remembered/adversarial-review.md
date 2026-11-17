# Adversarial review: verified mistake memory

**Scope:** Article, mobile edition, offline engine, optional LLM adapter, tests and CI. **Method:** code audit, locally reproduced attacks, regression tests, primary research cross-check. **Status:** educational example only, not a live-LLM benchmark.

## Verdict

The article correctly distinguishes external memory from model-weight updates. However, the original loader skipped verification of saved corrections, contradicting the “verify before remembering” design. Nine original tests passed while this bypass existed. The revised educational implementation passes **16 offline tests** and fails closed on several reproduced invalid-input cases. It remains unsuitable for deployment without a trusted storage and authorization layer.

## Confirmed vulnerabilities in original revision abf8174

| Finding | Severity if deployed with real actions | Reproduction | Remediation |
| --- | --- | --- | --- |
| Stored lessons bypass verifier | High | JSON correction `cyan` for `Last word: green purple` loads despite failing the oracle. | `load(path, verifier=...)` revalidates all persisted lessons. |
| Truthy but non-Boolean verifier responses accepted | High | `Verdict(1)` approves an incorrect correction. | Verify actual `Verdict` with Boolean `passed`. |
| Negative similarity threshold retrieves unrelated memory | Medium | `threshold=-0.5` returns unrelated lessons. | Enforce [0, 1]. |
| Gold evaluation labels could be false | Medium | Previous evaluator accepted arbitrary labels as ground truth. | Verify labels and predictions using independent oracle. |
| Loader bypassed schema/field checks | Medium | Raw `Lesson(**item)` admission without record-time checks. | Check types, text lengths, capacity and conflicts. |
| Medium mobile edition used automatic number syntax | Low | `1.` through `6.` risk auto-list formatting. | Change to plain `Risk One:` paragraphs. |

Attack reproductions and tests used Python 3.13, offline synthetic tasks. Severity assumes future integration with actual tools or private data; current demo has no such actions.

## Unresolved risks, explicitly tested and documented

**R1 — Guidance poisoning (high if instructions can be trusted).** The verifier checks a corrected answer, not guidance. Even with answer revalidation, a correct lesson can contain `Ignore all other instructions`. A negative regression test confirms this. Retrieved data must not gain tool permission or instruction priority. Require trusted approval of guidance and authenticated storage.

**R2 — Provenance spoofing (high).** `source="human"` is only an input label, not a signed approval. Correct answers do not prove that a human vetted the guidance or source.

**R3 — Scope spoofing (high).** Caller-supplied tenant `scope` filters data but provides no authentication or authorization; do not store private data.

**R4 — Toy measurement is tautological (research-critical).** The model is programmed to return the right word whenever *any* retrieved memory exists. The 0/2 to 2/2 result only verifies this branch on two same-template cases. No claim of generalization, LLM improvement, utility or efficiency is warranted.

**R5 — Staleness and false matching (medium).** Lexical overlap, no expiry or versioning, no policy applicability checks; apparently similar requests can require different answers.

**R6 — Operational limits (medium).** JSON is neither encrypted nor signed; simultaneous saves may overwrite data; very large inputs can consume memory before parsing; verifier exceptions propagate; optional paid model integration has not been tested in CI. `store=False` is not a zero-data-retention guarantee.

## Publication and research integrity

References checked: [Reflexion, NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html), [Self-Refine, NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/hash/91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference.html), [OpenAI Responses API guide](https://developers.openai.com/api/docs/guides/migrate-to-responses).

Run from `examples/verified-mistake-memory/`:

```bash
python -m pytest -q
python -m compileall -q memory_agent.py openai_demo.py
python memory_agent.py
```

Local offline outcome: **16 passed**, intentionally synthetic **0/2 memory off and 2/2 memory on**. These are neither real LLM measurements nor production security results. Before claiming learning gains, run a real-model, matched-budget, preregistered held-out benchmark with unrelated, changed-policy and adversarial families, including latency, error bars, regressions and dollar cost.

The mobile edition reduces auto-list risk; Android paste still cannot guarantee Medium-native heading formatting.
