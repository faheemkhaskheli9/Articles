# Your AI Agent Didn't Learn. It Just Remembered.

*How to build verified mistake memory for LLM agents—and test whether it actually prevents repeat errors.*

**By Faheem Khaskheli · November 17, 2026 · AI Engineering / LLM Agents / Python**

An AI agent makes a mistake. You correct it. Tomorrow, it gets a similar task, retrieves yesterday's correction, and produces a better answer.

Did it **learn**?

In one useful engineering sense, its *system behavior* adapted. But the language model's weights did not change. The application stored an example and inserted it into a later request. That distinction matters because adding memory is easy; proving that the memory helps on unseen tasks is much harder.

While working on my open-source [Brain project](https://github.com/faheemkhaskheli9/Brain), I built a provider-neutral prototype of this pattern: independently verified feedback, scoped episodic memory, bounded retrieval, and held-out evaluation. It is a research prototype, not a claim of human-like learning or improved production LLM accuracy.

This article explains the mechanism, provides a [standalone Python implementation](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/verified-mistake-memory), and, more importantly, shows where it can fail.

## Three things people call "learning"

**A better answer on the next turn:** A model may revise its output after feedback in the same conversation. The improvement may disappear when the conversation ends.

**Persistent external memory:** The application saves lessons, retrieves relevant ones for future tasks, and passes them back in context. This can change behavior across sessions, but the model's parameters remain fixed.

**Parameter learning:** Training procedures such as supervised fine-tuning or preference optimization change model weights. That is a different pipeline, with data governance, compute, evaluation, and rollback requirements.

The [Reflexion paper (NeurIPS 2023)](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html) demonstrated agents using verbal feedback in episodic memory without weight updates. [Self-Refine (NeurIPS 2023)](https://proceedings.neurips.cc/paper_files/paper/2023/hash/91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference.html) studied iterative feedback and revision with a model acting as its own reviewer. These are useful precedents, but neither means that an arbitrary saved reflection is a verified fact.

The practical question is narrower: **Can an independently checked correction reduce the same class of failure later, without creating new failures?**

## The failure mode: memory can preserve misinformation

Imagine a customer-support agent that incorrectly says refunds are allowed after 60 days. The agent writes itself a note: "Remember that refunds are allowed after 60 days."

Nothing about storing that sentence makes it true. If retrieval brings it back tomorrow, the agent may confidently repeat the original error.

The same problem appears in code agents that store fixes without running tests, research agents that save unsupported claims, and tool agents that interpret an API response incorrectly. An external memory system can turn a one-off error into a durable policy.

For a reliable pipeline, **the correction must be checked before it enters memory**, not merely after it is retrieved.

## The architecture: verify before remembering

The prototype follows this sequence:

1. The model answers a task.
2. An **independent verifier** checks the answer: a deterministic test, an authoritative tool, or a trusted human reviewer.
3. On failure, the verifier may propose a correction and a short lesson.
4. The proposed correction is **verified again**. A plausible correction is not automatically correct.
5. Only the approved lesson is stored with task context, scope, and provenance.
6. A later task retrieves a small set of relevant lessons, supplied as **lower-trust data**, not as new system instructions.
7. The later answer is checked independently. Success is measured on frozen, unseen tasks.

In the [Brain implementation](https://github.com/faheemkhaskheli9/Brain/blob/main/research/llm_mistake_learning.py), the model and verifier are separate callbacks. In the companion tutorial they remain separate, so you can test the feedback loop with no API key and optionally plug in a real model.

An important limitation: the application must actually control the verifier. If a model can mark its own answer "verified" and write into trusted memory, the gate is cosmetic. The companion now **revalidates every persisted answer during load** and rejects a verifier result that is not a real Boolean. This protects against some corrupted-memory cases, **not** against tampering with a correct lesson's guidance, a compromised verifier, or a forged provenance label. A trusted storage and review layer is still required.

## Build the smallest possible experiment

The companion project deliberately uses a synthetic task: given "Last word: green purple", return "purple". The offline model is programmed to return the *first* word unless it retrieves a lesson. The verifier independently extracts the required final word.

This is not exciting language modeling. That is the point: when the verifier, task, and failure are controlled, we can isolate memory mechanics instead of confusing them with general model capability.

The central call is short:

```python
from memory_agent import VerifiedMemory, oracle, solve, toy_model

memory = VerifiedMemory()
result = solve(
    "Last word: green purple",
    toy_model,
    oracle,
    memory,
    scope="demo",
)
print(result)
```

On the first attempt, the toy model responds "green." The verifier rejects it, independently confirms that "purple" is correct, and records the lesson. A second attempt with a relevant lesson returns "purple."

The example also includes atomic local JSON saving, capacity limits, strict provenance labels, scope-specific retrieval, conflict rejection, an optional OpenAI Responses API adapter, a VS Code debugger configuration, and tests. **It does not provide production-grade authentication or encrypted storage.**

## The result—and what it doesn't prove

The offline fixture evaluates two *different* word-pair tasks after recording the correction:

| Evaluation | Correct | Total |
|---|---:|---:|
| Deterministic toy, memory disabled | 0 | 2 |
| Deterministic toy, memory enabled | 2 | 2 |

The repository's 16 tests pass locally, including corrupted saved memory, invalid verifier verdicts, misleading retrieval thresholds, unverified gold labels, conflicting lessons, missing ground truth, and exact training/test leakage. An explicit negative test demonstrates that apparently correct feedback can still carry malicious guidance.

These numbers are **not an LLM benchmark**. The toy model was intentionally written to use any retrieved lesson to fix the exact type of error. Two examples do not estimate population accuracy, semantic generalization, real-world costs, or the quality of a production retrieval system.

A live-model adapter is included to show the integration point. Its results are not used to support the table.

## Adversarial review: six ways a memory system fools you

**1. The same model grades itself.** A fluent explanation of why an answer was wrong is not independent evidence. For deterministic workloads, use executable tests and reference data. For subjective work, use carefully designed human review or multiple evidence sources—without treating their agreement as proof.

**2. A fix is retrieved for the wrong task.** Similar wording does not imply identical policy. A lesson about one country's tax policy should not be applied to another. Retrieval should include explicit policy version, applicability conditions, and a safe fallback.

**3. Lessons cross user or tenant boundaries.** A `scope` string can filter demo data, but it is not authorization. Production systems need authenticated identity, access control, encryption, deletion, and audit trails.

**4. The memory contains an instruction attack.** Retrieved text is lower-trust material. Do not promote a stored lesson into a system or developer instruction, and never allow it to grant tool privileges. Prompt boundaries reduce risk but cannot guarantee immunity from injection.

**5. You evaluated on the mistakes you stored.** Training on "Last word: green purple" and later reporting success on that exact sentence tells you little about transfer. Freeze the held-out set before feedback collection and audit paraphrases and near-duplicates. The demo rejects exact overlaps only.

**6. Additional context costs more than it saves.** Each retrieval can add tokens, latency, false matches, and future maintenance work. Track benefit *after* verifier calls, retrieval, model retries, and rollback costs—not just the number of corrected answers.

A seventh failure deserves attention: a once-correct lesson can become stale. Version memories against tools, policies, and source data, and require an expiration or revalidation strategy before using them in consequential actions.

## How I would test this on a real LLM

First, construct a dataset of distinct task families with explicit correctness criteria. Split tasks by underlying scenario, not just by surface wording, and freeze the held-out set. Collect corrections only on the training side, using independent verifiers.

Then compare the *same* model and inference configuration across four settings: memory off, relevant verified memory, irrelevant or shuffled memory, and unverified memory in a sandbox. Match attempts and token budgets where feasible; report additional verifier and retrieval costs separately when exact matching is impossible.

Measure task success, repeat-error rate, new-error rate, retrieval precision, false-lesson application, latency, total model tokens, verifier expense, and regressions on previously solved tasks. Publish failures and uncertainty intervals. If a method only improves exact repeats while damaging changed-policy tasks, that is not enough to call it robust learning.

Finally, keep weight updates as a separate experiment. A curated memory may produce candidate supervised examples, but a fine-tuned checkpoint needs independent testing against the original model and a rollback criterion. **External memory is not fine-tuning.**

## Run the full example

Source: [Verified mistake memory — complete Python companion](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/verified-mistake-memory).

```bash
git clone https://github.com/faheemkhaskheli9/Articles.git
cd Articles/examples/verified-mistake-memory
python -m venv .venv
# Activate the virtual environment for your operating system
python -m pip install -r requirements.txt
python memory_agent.py
python -m pytest -q
```

The repository also includes `requirements-llm.txt`, `.env.example`, `openai_demo.py`, `.vscode/launch.json`, and a README explaining limitations and optional paid model calls. Run the offline version first; it does not require credentials.

The implementation is deliberately small enough to inspect. The challenging part is not serializing a lesson to JSON. It is **obtaining a trustworthy correction, proving relevance on the next task, and measuring whether the system's behavior improved without causing new errors**.

A model that retrieves a correction is not necessarily a model that has learned. But an application that consistently validates, remembers, and reuses corrections can still become more reliable—if its evaluation survives an adversarial test.

---

**Adversarial audit:** [Confirmed attack reproductions, fixes, and remaining risks](adversarial-review.md).

**Project basis:** [Brain — verified-feedback mistake learning](https://github.com/faheemkhaskheli9/Brain/blob/main/research/llm-mistake-learning.md) and [runnable source](https://github.com/faheemkhaskheli9/Brain/blob/main/research/llm_mistake_learning.py).

**Research:** [Reflexion (NeurIPS 2023)](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html) · [Self-Refine (NeurIPS 2023)](https://proceedings.neurips.cc/paper_files/paper/2023/hash/91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference.html).

**Publishing note:** For Medium Android, use the [mobile-safe text edition](medium-mobile.md) instead of copying Markdown code fences and tables directly. The Markdown file is the canonical source.
