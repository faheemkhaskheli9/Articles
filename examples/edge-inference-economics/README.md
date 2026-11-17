# Edge Inference Economics: Runnable Companion

A standard-library Python **what-if** calculator based on the annualized ownership-cost reasoning in [EdgeAI-CostBench](https://github.com/faheemkhaskheli9/EdgeAI-CostBench). This is an **independent pedagogical implementation**, not an ONNX benchmark, wattmeter or cloud price tracker.

**All sample values are hypothetical.** `items_per_second` is a user-supplied illustration, not collected from hardware. `useful_fraction_edge` and `useful_fraction_cloud` are assumptions, not measured task accuracy. The script refuses scenarios that claim measured provenance.

## Setup

Use Python 3.11+.

`python -m pip install -r requirements.txt`

Run the example:

`python cost_demo.py --config scenario.json`

Run utilization sensitivity including zero load:

`python cost_demo.py --config scenario.json --sweep`

Run the tests:

`python -m pytest -q`

No network, ONNX model, environment variables, API key or paid provider is needed. `requirements.txt` contains only the test dependency. `.env.example` is included to make the no-secrets contract explicit.

## VS Code

Open the **Articles** repository root in VS Code, choose a Python 3.11+ interpreter, then select **Edge economics — default** or **Edge economics — utilization sweep** in the Run and Debug panel. The included `.vscode/launch.json` uses repository-root paths.

## Model and boundaries

Annual cost = price/lifetime + annual maintenance + 8,760 h × (idle W × (1-u) + load W × u) / 1,000 × electricity tariff.

Useful items = items/s × 8,760 h × 3,600 s/h × utilization × assumed useful-result fraction.

Edge cost per million useful results = annual cost × 1,000,000 / useful items; undefined at zero utilization.

Cloud cost per million useful results = assumed price per million raw calls / assumed cloud useful-result fraction.

Break-even utilization solves edge annual cost ≤ cost of the *same number of useful items* through the assumed cloud price. `null` means it is not reached within 0–100% utilization or the question is undefined.

This demonstration excludes concurrency, traffic bursts, quality measurement, hardware benchmarking, actual power telemetry, network/cooling/taxes, downtime, and cloud fixed fees. In the main repository, use `edgecostbench run` for actual ONNX timing and `edgecostbench economics` for richer assumptions and reporting. Never treat a passed reference-output check as task accuracy.
