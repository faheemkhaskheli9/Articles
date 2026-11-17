Stop Making Your LLM Solve the Same Problem Twice

Build a validated reasoning cache in Python—with runnable code, tests, fallback logic, and an optional LLM procedure builder.

By Faheem Khaskheli · November 17, 2026 · AI Engineering / Python

Most AI agents spend money solving tasks that differ only in their input values. An invoice agent may calculate a discounted total, then ask a frontier model to repeat the same calculation for another customer. A conventional answer cache fails because the numbers have changed. The underlying procedure, however, has not.

Research published in November 2026, CPU-ARC: Agentic Reasoning Caching for on-CPU Reasoning Reuse (https://arxiv.org/abs/2611.09891), explores constructing reusable CPU-executable procedures from model reasoning traces. Its authors report 16–291× cheaper cache invocation than using the original model on their evaluated tasks. Those figures do not include all construction and production-serving expenses, and they are not a promise for your application.

In this tutorial, we will implement the engineering pattern, not reproduce the paper. The accompanying repository contains a fully runnable, deliberately narrow Python demo: a safe arithmetic procedure registry, strict request parser, independent reference tests, verified fallback, optional model synthesis, and VS Code debugging profiles.

RECOGNIZE THE KIND OF TASK WORTH CACHING

Our scenario is a checkout support agent. A customer asks:

Calculate checkout total: subtotal $120, discount 10%, tax 8%, shipping $5.

The business contract is exact: discount applies first; tax is calculated on the discounted subtotal; shipping is not taxable; monetary steps use two-decimal ROUND_HALF_UP rounding. Under those rules, the final result is $121.64.

Now a second customer asks:

Compute total: shipping $0, tax 8%, discount 15%, subtotal $200.

The final amount is $183.60. The inputs and wording changed, not the procedure. A generic model could reason again; a verified cached procedure can execute cheaply on the CPU.

There is an important engineering caveat: if the business rules are already known, simply implement a normal Python function. Agentic reasoning caching becomes interesting when agents repeatedly encounter many unanticipated task families and can derive reusable, testable procedures from earlier solutions.

SEPARATE INTERPRETATION FROM EXECUTION

Our minimal architecture uses three components: a router that refuses unfamiliar requests; a registry of approved arithmetic steps; and a deterministic evaluator. A request that cannot safely use the procedure goes through a verified fallback rather than a forced cache hit.

Because language similarity does not imply identical business rules, we require explicit field names and reject unknown clauses. For example, “tax the shipping fee” must not reuse a procedure that assumes shipping is tax-exempt. A production semantic retriever may shortlist candidate procedures, but it still needs a stricter applicability check before execution.

Input parsing produces the four validated values subtotal, discount, tax, and shipping. No LLM is necessary for the example's intentionally structured requests. A small extraction model is reasonable when natural-language variation becomes too broad for a strict parser.

ENCODE THE PROCEDURE AS CONSTRAINED, INSPECTABLE STEPS

A response cache stores “$121.64.” Our procedure cache stores a parameterized calculation. Each expression is represented as data, not executable Python code:

Reusable procedure: four arithmetic steps calculate discount amount, taxable subtotal, tax amount, and final total. Each step is expressed using named inputs in a restricted, inspectable arithmetic language.

The companion evaluator parses each expression into a Python abstract syntax tree (AST), then permits only numeric literals, known variable names, arithmetic operators, and parentheses. It rejects imports, attribute access, calls, list literals, exponentiation, excessive complexity, and out-of-bounds intermediate values.

It performs calculations with Decimal and applies the configured rounding policy after each step. This makes the procedure inspectable and repeatable. It does not turn arbitrary model-generated code into a secure sandbox; production-generated code requires stronger isolation.

RUN THE WORKING EXAMPLE

The code, installation files, tests, debugger configuration and optional model builder live in the reasoning-cache example (https://github.com/faheemkhaskheli9/Articles/tree/main/examples/reasoning-cache).

Use Python 3.11 or newer. From a terminal:

Setup: clone the Articles repository, open examples/reasoning-cache, create a Python 3.11+ virtual environment, install requirements.txt and the editable package, then run python -m reasoning_cache --seed. Exact copyable commands are in the project README.

The --seed option installs a curated, validated procedure. It runs offline and needs no API key. The CLI prints the routing decision and calculated values.

Try changed parameters:

To test different values, run the CLI with --request followed by: Compute total: shipping $0, tax 8%, discount 15%, subtotal $200.

Expected output includes:

Expected result: route is cache; procedure is checkout-v1; discount amount is 30.00; taxable subtotal is 170.00; tax amount is 13.60; and total is 183.60.

Delete the cache file and run the same request without --seed. The demo returns verified_fallback from an independent reference implementation instead of fabricating a cache hit. A general-purpose agent might invoke its original model here, but this narrowly scoped demo deliberately avoids calling an LLM for routine checkout arithmetic.

OPTIONAL: HAVE AN LLM PROPOSE THE REUSABLE PROCEDURE

The more interesting part of the CPU-ARC idea is building a procedure from a previously solved task. Our optional builder illustrates that loop without executing arbitrary generated Python. It makes two model calls: one to solve an example and another to propose a JSON arithmetic program. It then subjects the candidate to syntax constraints and independent reference tests before saving it.

Copy .env.example to .env, configure OPENAI_API_KEY and optionally OPENAI_MODEL, then run:

Optional model builder command: python -m reasoning_cache --build. This requires setting OPENAI_API_KEY in .env and makes paid model calls.

This uses a paid API and can fail validation. That is intentional: a builder's output is a candidate, not an automatically trusted skill. The demo does not generalize to unrestricted problems or implement the source paper's full semantic-function retrieval and training loop.

Notice the distinction: our independent reference function defines the correct checkout policy. A genuine discovery system may not already possess such an oracle. Its hardest problem is discovering reliable tests for newly synthesized capabilities.

TEST THE FAILURE PATHS, NOT ONLY SUCCESSFUL CALCULATIONS

Run the test suite:

Testing command: python -m pytest -q.

The checked-in tests cover changed parameter ordering, percentage bounds, duplicate fields, missing values, unsupported tax policies, dangerous expression syntax, corrupted cache files, and incorrect generated procedures. In this educational workload, a false cache miss wastes an opportunity; a false cache hit can generate an incorrect financial result. Those are not equivalent errors.

Experienced engineers should distinguish four validation layers:

Request contract: Are all required inputs present and is the policy applicable?

Expression safety: Does the proposal use only the permitted language subset?

Independent correctness: Does it pass known examples, boundary cases and invariants?

Operational constraints: Is the procedure still current, approved, observable, and reversible?

Even passing tests cannot prove a procedure is correct for every input. For high-risk or changing domains, require stronger review, fuzzing, isolated execution and human approval.

THE EXPERT QUESTION: WHEN DOES CACHING ACTUALLY SAVE MONEY?

Cache-hit rate alone is not a business metric. Building the procedure costs money; routing each incoming request costs money; and some requests will miss or fail verification.

A simplified break-even estimate is:

Break-even rule: required future request count must exceed the one-time build cost divided by the expected net saving per request. Expected savings depend on validated cache-hit rate, source-model cost, cached execution cost, and routing cost.

If the denominator is zero or negative, the procedure never pays back its construction cost under those assumptions. If the cost of a wrong answer is substantial, expected error cost should enter the equation too.

In production, monitor verified cache-hit rate, end-to-end latency (including routing), amortized construction cost, invalidation rate, incorrect-match rate, fallback cost, and distribution drift. Version the registry. Tie each procedure to policy and data versions. Treat a model-generated function as a software artifact that needs tests, provenance, ownership, and rollback.

For recurring deterministic workflows, ordinary code is usually best. For novel scientific problems, it may be impossible to safely reuse a cached procedure. Between those extremes lies the interesting space: repeated problem families where an agent can learn reliable executable capabilities from past work.

The goal is not to make every AI agent use a cache. It is to make an agent recognize when expensive reasoning has already produced a reusable, verified procedure.

RESEARCH AND IMPLEMENTATION

Research: Peter Belcak, Greg Heinrich, Saurav Muralidharan, Shizhe Diao, and Pavlo Molchanov. CPU-ARC: Agentic Reasoning Caching for on-CPU Reasoning Reuse (https://arxiv.org/abs/2611.09891). arXiv preprint, November 6, 2026.

Complete code: GitHub repository — dependencies, .env.example, tests, and VS Code launch profiles (https://github.com/faheemkhaskheli9/Articles/tree/main/examples/reasoning-cache).

Scope: This example demonstrates a tightly constrained interpretation-execution-validation pattern; it is not the paper's implementation. The reported research cost ratios are not measured by this demo.

Complete source and setup: https://github.com/faheemkhaskheli9/Articles/tree/main/examples/reasoning-cache
