# Are We Wasting Billions of Parameters Storing Knowledge?

*Can external knowledge make language models smaller without sacrificing reasoning?*

A language model learns grammar, facts, procedures, abstractions and patterns of reasoning through overlapping parameters. This raises an engineering question: should a neural network memorize every fact it may ever need, or should it learn how to use evidence supplied by an external memory?

The evidence supports a qualified answer: retrieval can replace considerable neural capacity on some knowledge-intensive workloads. It has not been shown to replace general reasoning capacity.

## The evidence

DeepMind's [RETRO (ICML 2022)](https://proceedings.mlr.press/v162/borgeaud22a.html) used a two-trillion-token datastore. Its 7.5B-parameter model achieved language-modeling performance comparable to much larger GPT-3 and Jurassic-1 models on The Pile, with roughly 25 times fewer parameters. Perplexity is not a measure of general reasoning equivalence.

[Atlas (JMLR 2023)](https://www.jmlr.org/papers/v24/23-0037.html) achieved 42.4% on Natural Questions with an 11B model and 64 training examples, compared with 39.6% for 540B PaLM. Different training and architectures prevent a causal attribution of that entire difference to retrieval.

[Mallen et al. (ACL 2023)](https://aclanthology.org/2023.acl-long.546/) found that retrieval is particularly useful for obscure entities, while increasing model size mainly helped popular facts in their experiments.

[MassiveDS (NeurIPS 2024)](https://arxiv.org/abs/2407.12854) scaled external memory to 1.4 trillion tokens and found that smaller retrieval-enhanced models could outperform larger closed-book models on knowledge-intensive tasks.

[Knowledge Capacity Scaling Laws (ICLR 2025)](https://arxiv.org/abs/2404.05405) estimated approximately two bits of factual knowledge per parameter in controlled settings. [How much can language models memorize? (ICML 2026)](https://proceedings.mlr.press/v306/morris26a.html) estimated about 3.6 bits per parameter under a different experimental definition. Neither result establishes what fraction of real-world LLM parameters is exclusively factual storage.

[To Memorize or to Retrieve (April 2026 preprint)](https://arxiv.org/abs/2604.00715) varied pretraining and retrieval budgets across 30M–3B models. Benefits depended on the task and scale. The study used a shared 8B embedding model, so generator size alone understates whole-system resource requirements.

[Knowledgeless Language Models (July 2026 preprint)](https://arxiv.org/abs/2607.12831) anonymized named entities during pretraining to suppress entity-linked recall. At matched model sizes, the authors reported improved contextual QA and verification, with up to 20–25% relative gains under some noisy retrieval conditions. This is promising evidence for a different training objective, not proof of general reasoning parity or a universal compression ratio.

## The strongest counterargument

A database can supply a premise, but it cannot ensure that a generator understands or correctly applies the premise.

[Can Small Language Models Use What They Retrieve? (March 2026 preprint)](https://arxiv.org/abs/2603.11513) evaluated 360M–8B models on Natural Questions and HotpotQA. For the tested models up to 7B, even oracle passages failed to rescue 85–100% of questions initially answered incorrectly. This is a setting-specific result, not a universal lower size bound. Retrieval-trained models may behave differently.

[Finding the Minimal Parameter Budget for Implicit Reasoning (ICML 2026)](https://proceedings.mlr.press/v306/wang26hf.html) relates the required neural capacity for implicit multi-hop inference to synthetic graph-search complexity. Reasoning itself has a capacity cost. Its numerical scaling law should not be extrapolated directly to general intelligence.

Moreover, [Lost in the Middle (TACL 2024)](https://aclanthology.org/2024.tacl-1.9/) shows that evidence position and context length can affect performance.

## A modular architecture

Retain language, foundational concepts, reusable inference patterns, tool selection and uncertainty estimation in a reasoning core. Externalize volatile facts, entity attributes, long-tail reference material and domain-specific records.

A request flows through a query planner, a domain router, a versioned text/SQL/graph retrieval layer, a compact reasoner and an evidence verifier. The controller can retrieve again, abstain or escalate to a larger model. The verifier must not be assumed independent or infallible; use deterministic checks where possible. Treat retrieved documents as untrusted data and enforce permissions before retrieval.

A plug-in should expose a common contract for search, structured lookup, provenance, version and validity dates. Swapping a medical reference module for a software documentation module should require no change to reasoning weights. This is a hypothesis, not an established ability.

Train for evidence use rather than simply removing documents. Compare standard pretraining against retrieval-aware training, entity anonymization with consistent within-document identities, procedural examples, counterfactual facts, missing evidence, distractors, and supervised or reward-based training with verifiable outcomes. Keep foundational concepts and relational structures. Anonymization can damage semantics, so measure its side effects.

## A falsifiable experiment

First run a pilot with same-family 1.5B, 3B and 7B models; add a 14B or larger comparator on suitable hardware. Compare every size with no context, ordinary retrieval, oracle evidence, distractors and counterfactual evidence. Use a frozen corpus, identical context limits, matched decoding and pinned checkpoints. Repeat over held-out tasks.

Evaluate independently:
- factual QA with held-out entities and newly generated facts;
- multi-hop inference with all premises supplied, graph depths and rules varied;
- math, code and logic with unseen procedural tasks and deterministic answer checks;
- domain transfer by swapping the knowledge store without changing weights;
- abstention, stale/conflicting evidence, prompt injection and unavailable retrieval.

Record closed-book accuracy, oracle rescue rate among closed-book failures, damage rate among closed-book successes, end-to-end accuracy, evidence recall, groundedness, p50/p95 latency, peak accelerator and host memory, index storage, embedding/index build cost, and cost per correct answer. Include retrieval and verification model parameters and inference calls. Report paired confidence intervals and per-task results; repeated synthetic variants from one world are not independent, so bootstrap by world.

Second, train matched small models from scratch on the same tokenizer and architecture family, controlling training tokens, compute, data quality and retriever capacity. Vary the fraction of facts held out in the external store separately from the amount of reasoning supervision. Include matched-size and matched-compute baselines. Use secret randomized test worlds with rules and facts not in training, and prevent benchmark solutions from entering retrieval.

A practical preregistered success criterion: a generator at most half the baseline size with a 95% paired confidence interval for the accuracy difference entirely above -2 percentage points on every primary reasoning suite, non-inferior factual accuracy with retrieval, and lower measured cost per correct answer at the target throughput. These are proposed margins, not measured outcomes; determine sample size before evaluation.

If oracle evidence fails, improve reasoning/evidence integration rather than the search engine. If smaller models match factual QA but fail novel reasoning, the general compression claim is rejected. If the generator shrinks but total latency or cost rises, the deployment claim fails.

## Economics

Raw weight bytes approximately equal parameters times bits per weight divided by eight. A 7B dense model needs about 3.5 GB of ideal 4-bit weights versus 35 GB for 70B at the same precision; actual memory includes quantization metadata, activations, runtime and KV cache. An illustrative million 768-dimensional float32 embeddings require about 3.07 GB before index overhead or source text. External memory is often cheaper to store on CPU or disk, but retrieval, reranking, longer prompts and additional model calls are not free.

## Conclusion

Some factual memorization can be externalized. The amount of neural capacity that can be removed without losing reasoning remains an open empirical question. The research opportunity is to discover the minimum sufficient reasoning core under a realistic total system budget, not to build a knowledge-free neural network.

This article is a literature synthesis and proposed experiment, not a report of original benchmark measurements. The 2026 arXiv studies are preliminary; the earlier conference and journal results are task-specific.
