# Validated Reasoning Cache: Runnable Example

This is an **educational analogue** of procedural reasoning reuse inspired by CPU-ARC, **not** a reproduction of CPU-ARC or a general-purpose agent. The checkout policy is intentionally fixed: discount first, tax on discounted subtotal, shipping is not taxable, ROUND_HALF_UP for monetary steps.

## Requirements

Python 3.11+, pip. VS Code + Python extension optional. An OpenAI API key is required **only** for model-assisted `--build` and incurs API charges.

## Set up

```bash
cd examples/reasoning-cache
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

Copy `.env.example` to `.env` only if using `--build`. Never commit `.env`.

## Offline demo (no API key)

```bash
python -m reasoning_cache --request "Calculate checkout total: subtotal $120, discount 10%, tax 8%, shipping $5."
# route: verified_fallback
python -m reasoning_cache --seed
# route: cache (validated, curated procedural steps)
python -m reasoning_cache --request "Compute total: shipping $0, tax 8%, discount 15%, subtotal $200."
# result.total: 183.60
```

## Optional LLM builder

```bash
cp .env.example .env   # or copy manually on Windows
# Edit .env and supply an API key
python -m reasoning_cache --build
```

This issues **two** model requests (source solution + builder). The builder returns a constrained JSON arithmetic program, **not arbitrary Python**. Its output must pass AST restrictions and independent reference test cases before being saved. It does not improve the closed-form checkout calculation over directly coding it; this stage illustrates the construction-validation loop.

## Tests / VS Code

```bash
python -m pytest -q
```

Open the **repository root** in VS Code, select the example's `.venv` Python interpreter, and use one of three profiles in `.vscode/launch.json`. Create `.env` for debugger profiles if VS Code needs it.

## Production boundaries

The DSL avoids dynamic `exec`/`eval` but does not constitute a security sandbox. Do not run untrusted arbitrary Python. A real system needs isolated worker execution, audited policies, generated test corpus, policy invalidation, model/output observability, budget controls, resource isolation, concurrency handling, and human approval for consequential procedures. Routing here intentionally fails closed for unsupported free-form requests. When inputs do not match, parsing rejects them rather than silently assuming a procedure applies. No latency or dollar-saving claims are made for this demo.
