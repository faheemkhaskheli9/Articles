# Plug-and-Play Domain Memory for LLMs: Pros, Cons, and Adversarial Review

**Date:** 2026-11-18  
**Status:** Design review and research hypotheses, not an implemented benchmark  
**Companion article:** [Can We Build an LLM with a Separate Brain and Plug-and-Play Knowledge?](article.md)

## Executive verdict

**Proceed as a focused research experiment, not as a claim that external memory can replace an LLM's learned domain competence.**

The strongest near-term value is in **separately versioned knowledge, provenance, and controlled updates**. The weakest claims are that the approach automatically produces a smaller, cheaper, faster, safer, or more intelligent system. Modular retrieval is not new: a publishable contribution needs matched-budget experiments demonstrating capabilities or reliability beyond strong RAG and long-context alternatives.

**Recommended research thesis:** *Can a frozen LLM use versioned, independently maintained domain knowledge packages with measurable improvements in update consistency and cross-domain isolation, without unacceptable retrieval, verification, and inference overhead?*

## 1. Benefits: what is real and what is hypothetical

| Proposed advantage | Mechanism | Evidence level / caveat | Verdict |
| --- | --- | --- | --- |
| Update facts without retraining | Replace and re-index external evidence | Standard external-retrieval capability; not new by itself | **Strong engineering advantage** |
| Mount/unmount specialized domains | Common API and registry for domain packages | Straightforward for text retrieval; model-specific learned adapters are not universally portable | **Strong engineering advantage** |
| Preserve provenance | Carry source, version, passage, publication date, permissions | Works only when inputs and metadata are trustworthy and answers actually use cited evidence | **Strong when designed well** |
| Customize retrieval per domain | Code symbol search, formula lookup, hybrid passage search, clinical guideline filters | Domain-specific search engineering may improve relevance; requires measurement | **Plausible** |
| Improve knowledge freshness | Versioned sources can supersede older documents | Model may still rely on outdated parametric knowledge or stale caches | **Conditional** |
| Share a frozen model across domains | Reuse inference engine; select packages at runtime | Does not imply equal expertise in all domains | **Strong for operations, limited for intelligence** |
| Avoid repeated fine-tuning for documentation | Update index and source assets instead of weights | Doesn't replace fine-tuning that teaches capabilities or style | **Strong for factual updates** |
| Support auditable knowledge changes | Package version, provenance, rollback, signed manifests | Requires robust lifecycle, tests, and access controls | **Useful for governance** |
| Reduce parameter count | Outsource some factual information to retrieval | Retrieval does not automatically replace procedural competence; no general size equivalence established | **Unproven research hypothesis** |
| Reduce hallucinations | Supply high-quality evidence and abstention behavior | Retrieved evidence can be wrong, conflicting, ignored, or mis-cited | **Conditional** |
| Reduce total inference cost | Route only when needed and constrain context | Routers/rerankers/verifiers can exceed saved token cost | **Unproven** |
| Improve multi-domain reasoning | Coordinate several specialized sources | Concatenation is not reasoning; multi-source conflicts add complexity | **Unproven** |

## 2. Structural disadvantages

### 2.1 There is no clean "reasoning-only" model

Weights encode intertwined facts, concepts, representations, language competency, and computational behaviors. Externalizing evidence does not erase parametric knowledge, and a small model can fail even when correct evidence is provided. A package interface separates **storage and retrieval** from **generation** in software; it does not prove a clean neuroscientific or mechanistic decomposition of learned knowledge and reasoning.

**Mitigation:** freeze the base model; compare normal retrieval to *oracle-provided relevant evidence*. Failures under oracle evidence identify limitations that retrieval engineering alone cannot fix.

### 2.2 Quality is capped by retrieval *and* evidence use

A correct document may never be retrieved; a retrieved passage may lack assumptions or units; an LLM may ignore it. Long contexts do not reliably eliminate this problem. The 2025 ICML LaRA study found that the best choice between RAG and long-context strategies depends on task and model conditions.

**Mitigation:** measure evidence recall, passage sufficiency, evidence utilization, and answer correctness separately.

### 2.3 Conflicts between source packages

Different medical guidelines, library versions, or physics experiments may disagree legitimately. Ranking by vector similarity cannot determine which source is applicable. The 2025 EMNLP MAGIC benchmark highlights difficulty detecting conflicts, especially in multi-hop scenarios.

**Mitigation:** scope-aware versioning, source quality metadata, explicit contradictory-claim representation, and abstention if evidence cannot be reconciled.

### 2.4 Latency and operational burden

A query may invoke a domain router, two indexes, a reranker, conflict resolution, reasoning generation, and a verifier. Performance can degrade with remote network calls, cold starts, cross-package retrieval, and re-embedding.

**Mitigation:** route to no retrieval when appropriate; batch retrieval; cache by query and package version; benchmark *full request latency and cost*, not just output tokens.

### 2.5 The plug-in becomes a security boundary

Documents and package manifests can be altered. Attackers can poison retrieval, insert behavioral instructions into source text, smuggle data across access-control boundaries, or manipulate ranking. OWASP documents these RAG-specific attack surfaces.

**Mitigation:** signed or authenticated package manifests, content hashes and approvals, ACL filtering before retrieval, isolation of source data from tool permissions, immutable audit logs, and tests for prompt injection. Hashes confirm integrity only against an authorized baseline, not truthfulness of the baseline.

### 2.6 Heterogeneous data is expensive to normalize

A chemistry property table, a code example, a mathematical derivation, an astronomy observation, and a medical guideline have different semantics. A single embedding schema loses structure.

**Mitigation:** a narrow **common evidence envelope** (content, source, version, scope, permissions), with domain-owned internal schemas and retrieval implementations. Do not mandate graphs or learned adapters before demonstrating a need.

### 2.7 High-stakes medical use requires more than "medical memory"

Clinical facts may be contextual, jurisdiction-specific, time-sensitive, and affected by individual circumstances. A retrieved guideline is not patient-specific clinical reasoning. Protected health information adds privacy constraints.

**Mitigation:** initially treat medicine as a *read-only research corpus*, not an autonomous clinical-decision system; add expert-reviewed evaluation and authorization controls before any consequential deployment.

### 2.8 A new module may not help at all

If the base model knows the fact already, retrieval may produce identical quality at increased cost. For common questions, the best policy may be to avoid retrieval.

**Mitigation:** add a no-retrieval baseline and measure marginal utility per request category.

## 3. Attack matrix: the strongest possible objections

| Attack | Adversary setup | What failure reveals | Required defense/test |
| --- | --- | --- | --- |
| **A. Oracle knowledge** | Supply perfect gold passages to a frozen small model for difficult questions | Knowledge access is not reasoning competence | Compare base, RAG, and oracle-evidence accuracy |
| **B. Version conflict** | Physics or code package v1 and v2 give incompatible information | Stale data or incorrect applicability rules | Version-specific answers, temporal correctness, conflict detection |
| **C. Module contamination** | Mount an irrelevant software package before asking medical/physics questions | Cross-domain interference | Unrelated-domain regression test with fixed decoding settings |
| **D. Cross-domain reasoning** | Solve MRI, battery, or telescope tasks requiring several domains | Naive retrieval concatenation is insufficient | Multi-package vs merged-corpus vs oracle multi-domain evidence |
| **E. Prompt injection** | One retrieved passage says to ignore rules or invoke privileged tools | Untrusted evidence crosses instruction boundary | Red-team malicious passages, enforce tool ACLs independently |
| **F. Citation laundering** | A passage has related words but does not support the claim | Citations become decoration rather than evidence | Human-adjudicated claim-to-passage support precision |
| **G. Router bypass** | Rephrase or disguise domain terms; mix multiple domains | Relevant modules never run | Multi-label routing precision/recall and false-negative analysis |
| **H. Model incompatibility** | Swap embeddings or a neural adapter between different model families | "Plug-and-play" promise is underspecified | Contract and compatibility testing; text packages vs adapters clearly separated |
| **I. Hidden cost** | Route, rerank, and verify 3–5 times on a simple factual question | Claimed efficiency is false | P50/P95 latency, cost/request, energy proxy and total compute |
| **J. Privilege leak** | A user retrieves a cross-tenant document via shared vector index | Fatal authorization failure | ACL filtering *before* ranking; isolation/integration tests |
| **K. Knowledge deletion** | Uninstall package after index, caches, and logs are populated | Data persists despite removal promise | Versioned cache invalidation and data-retention audit |
| **L. Benchmark leakage** | Evaluation questions or reference answers are ingested into packages | Inflated performance | Holdout by document/source/time; audit ingestion; report overlap |
| **M. Poisoned authoritative source** | Attackers alter a trusted but compromised document | Metadata alone does not establish truth | Content review, hashes, signatures, source trust and multi-source corroboration |
| **N. Small-model ceiling** | Compare quantized 3B and stronger models under gold evidence | Ability gap cannot be retrieved away | Model-scale × evidence-quality factorial experiment |

## 4. Strongest skeptical conference review

**Claim 1: "We separate reasoning from knowledge."**  
**Rebuttal:** We separate one class of external evidence from model inference at the system level. Neural capabilities remain interdependent; avoid claiming clean mechanistic separation.

**Claim 2: "Plugging in domains makes a model an expert."**  
**Rebuttal:** No. An LLM can retrieve expert material without possessing expert interpretation, decision-making, or validation capability. Expert performance must be benchmarked.

**Claim 3: "The architecture is novel."**  
**Rebuttal:** Domain-specific RAG, routing, modular memory, adapters, and self-reflective retrieval already exist. Novelty must be a demonstrated new algorithm, formal contract with measured guarantees, or independently reproducible reliability gain.

**Claim 4: "The architecture uses fewer compute resources."**  
**Rebuttal:** A frozen model still processes retrieved tokens and tool outputs. Retrieval infrastructure, rerankers, verifiers, and cache invalidation have costs. Require full-stack comparisons at matched quality.

**Claim 5: "Source citations prevent hallucinations."**  
**Rebuttal:** Cited text may be irrelevant, malicious, outdated, or misread. Evaluate claim support and abstention.

**Claim 6: "The architecture provides continual learning."**  
**Rebuttal:** Changing an external index provides knowledge access or behavior adaptation, not necessarily durable changes to model parameters or transferable skills. Use terminology carefully.

## 5. Alternative designs worth comparing

| Alternative | Relative strengths | Relative weaknesses | Test against proposed architecture |
| --- | --- | --- | --- |
| **One strong hybrid RAG index** | Simple, mature, often cheaper | Weaker isolation and package governance | Primary baseline |
| **Long-context prompting** | No dedicated retrieval failures on modest corpora | Context cost; attention/placement limits; freshness challenges | Matched document budget |
| **Domain prompt / tools only** | Cheap for low-complexity guidance and deterministic operations | Limited extensive factual recall | Lightweight baseline |
| **Domain fine-tuning or LoRA** | Can change output habits and domain-use capabilities | Training and compatibility overhead; difficult updates | Secondary baseline |
| **Mixture-of-experts / specialized models** | Potential compute/capability specialization | Multiple models, training/routing complexity | Later comparison |
| **Package-based RAG (proposal)** | Versioning, governance, isolation, tailored retrieval | Registry, routing, conflicts, cache, security and latency overhead | Main treatment |
| **Hybrid package + specialized tools** | Exact code execution, math, database filtering; factual evidence | More interfaces and failure surfaces | High-potential future extension |

Existing work shows that memory and external retrieval are active, broad fields. A 2026 modular-memory position paper proposes combining in-context and in-weight learning; it does not establish that every domain package architecture produces accuracy gains.

## 6. What to build first

Start with three manageable domains: **software engineering, physics, and chemistry**. Treat medicine as a subsequent high-stakes validation domain, not the initial demonstration.

**Minimum implementation:**

- One frozen answer model (same checkpoint and decoding for all conditions).
- A manifest-based package registry.
- Per-package hybrid retrieval and source/metadata envelope.
- Multi-label router with explicit "no retrieval" decision.
- Version and authorization filtering *before* retrieved text enters context.
- Deterministic or independently adjudicated validators where available.
- Logging of selected modules, evidence hashes, token counts, latency, decisions, and outcomes.

**Avoid initially:** custom transformer training, dozens of packages, graph databases everywhere, learned neural memory adapters, and unsupported claims that a lightweight LLM has general expert competence.

## 7. Preregistered experiment design

### Conditions

1. Frozen model, no retrieval.
2. Frozen model + one merged hybrid RAG index.
3. Frozen model + modular packages, oracle-selected domain.
4. Frozen model + modular packages, automatic domain routing.
5. Condition 4 + version/conflict controls.
6. Frozen model + **oracle evidence** (retrieval upper-bound study).
7. Optional: long-context and domain-LoRA baselines at matched task and resource budget.

Use fixed test splits, evaluate several model sizes if feasible, and avoid reusing test questions for routing development.

### Primary metrics

| Category | Metric |
| --- | --- |
| Task success | Exact correctness / domain-specific rubric accuracy |
| Evidence | Recall@k, sufficiency, human-audited claim support |
| Knowledge updates | Correctness after changed source, stale-answer rate, rollback correctness |
| Isolation | Difference on unrelated-domain held-out evaluation |
| Routing | Multi-label precision/recall; unnecessary retrieval frequency |
| Conflict handling | Correct applicable version; contradiction identification; appropriate abstention |
| Security | Prompt-injection attack success; cross-tenant leakage; unauthorized tool actions |
| Operations | P50/P95 latency, token usage, storage, retrieval calls, peak RAM/VRAM, total cost |

### Thresholds: proposed gates, *not measured results*

- **Required:** no statistically supported deterioration in unrelated-domain correctness compared with matched RAG, within a prespecified 1-point non-inferiority margin.
- **Required:** demonstrably better stale-information handling or source-version correctness than merged-corpus RAG.
- **Required:** package unload and rollback must invalidate version-bound caches and prevent unauthorized access.
- **Required:** no unauthorized tool execution or cross-tenant disclosure in the controlled security test suite; this does not prove universal security.
- **Tradeoff gate:** additional end-to-end latency and cost must be justified by significant reliability gains; do not impose arbitrary savings claims.
- **Research gate:** if modular packages provide only packaging convenience and no measurable reliability or update advantage over strong RAG, frame the outcome as systems engineering, not an LLM breakthrough.

Report uncertainty intervals, paired analyses, latency distributions, and negative results. Evaluate retrieval and reasoning separately.

## 8. Feasibility and prioritization

| Candidate contribution | Novelty potential | Practical difficulty | Priority |
| --- | --- | --- | --- |
| Versioned external knowledge and provenance | Low on its own | Low–medium | Build as infrastructure |
| Memory isolation and update-consistency benchmark | Medium–high if novel benchmark/tasks and rigorous baselines | Medium | **P0** |
| Conflict-aware multi-package controller | Medium, depends on approach and results | Medium–high | **P1** |
| Adaptive routing with total-cost optimization | Medium, if improvement is demonstrated | Medium | **P1** |
| Multi-domain evidence composition | Medium–high, if new method and real gains | High | **P2** |
| Model-agnostic learned neural memory plug-ins | Potentially high but difficult; architecture mismatch limits interchangeability | Very high | **Later** |

**Suggested falsifiable thesis:**  
*"On held-out source updates, a version-aware modular retrieval controller reduces stale or cross-domain-contaminated answers relative to a matched merged-index hybrid RAG system, without material unrelated-domain regression."*

**Kill criteria:** Stop adding architectural layers if oracle evidence reveals the generator is the bottleneck; if a strong merged-index RAG catches up after comparable version filtering; or if the added components worsen accuracy and operating cost without compensating reliability.

## 9. Source notes (verified links)

- [Dorovatas et al., *Position: Modular Memory is the Key to Continual Learning Agents*, ICML 2026](https://proceedings.mlr.press/v306/dorovatas26a.html) — conceptual motivation; distinguishes in-context and in-weight learning.
- [Lee et al., *MAGIC: A Multi-Hop and Graph-Based Benchmark for Inter-Context Conflicts in RAG*, Findings EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.466/) — empirical study of conflict detection difficulties.
- [Li et al., *LaRA: Benchmarking RAG and Long-Context LLMs*, ICML 2025](https://proceedings.mlr.press/v267/li25dv.html) — task-dependent RAG versus long-context tradeoffs.
- [OWASP, *RAG Security Cheat Sheet*](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html) — document poisoning, embedding manipulation, access control, provenance, and prompt injection mitigations.
- [*Learning to remember: advances in memory mechanisms for large language models* (2026 survey)](https://link.springer.com/article/10.1007/s44336-026-00044-1) — broad memory taxonomy and lifecycle limitations.

## Final recommendation

**Build this as a controlled memory-system experiment before presenting it as a new LLM architecture.** Package-based domain knowledge has clear operational advantages; the defensible research contribution is quantifying and improving update correctness, conflict handling, isolation, and cost. The strongest adversarial test is still simple: **if the frozen model fails with perfect evidence, no memory interface alone can cure the reasoning gap.**
