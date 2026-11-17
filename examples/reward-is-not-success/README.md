# Reward is not success: a paired simulation

This educational, offline Python experiment illustrates why **proxy progress reward** and **goal completion** are different evaluation metrics. It was inspired by the independent results in [`Brain/research/continuous-motor-results-2026-11-12.md`](https://github.com/faheemkhaskheli9/Brain/blob/main/research/continuous-motor-results-2026-11-12.md), but **does not reproduce that neural controller, dataset, task, architecture, or measurements**.

## Run

Python 3.10+:

```bash
cd examples/reward-is-not-success
python -m pip install -r requirements.txt
python reward_gap.py --episodes 200 --seed 42 --steps 16 --slip-rate 0.30
python reward_gap.py --stress-test
python -m pytest -q
```

All simulation code uses the Python standard library. `pytest` is only a test dependency. No API keys, network access, or external datasets are needed. `.env.example` documents that no secrets or environment variables are required. Open this example directory in VS Code to use `.vscode/launch.json`.

## Design

- Each episode starts at position 0 with goal position 1 and a hard 16-step deadline.
- `cautious` moves toward the goal by 0.04 (or 0.02 on a slip): it usually gets a positive per-step progress score, but cannot cover enough distance in 16 steps.
- `bold` moves by +0.14 (or -0.06 on a slip, clamped at zero): some actions move away from the target, reducing its progress score, but it can finish the task.
- Progress reward is +1 when distance decreases, -1 when it increases, and 0 when distance is unchanged. **This reward has no terminal success bonus**.
- Once a policy touches the target, it holds position; unused remaining step slots contribute 0 reward. Both policies are evaluated with the same horizon and the *same pre-sampled slip tape* in each paired episode. **This specifically depresses the per-slot reward of fast finishing policies, because completed episodes cannot collect more progress points. It is a deliberate teaching construction, not a generally valid task reward.**
- Report proxy reward/action-slot, fraction of episodes with goal contact, and remaining distance. The seeds are deterministic for debugging, not a claim of statistical significance.

## Adversarial interpretation

This deliberately exposes a reward-design failure using handcrafted policies. They are not trained agents and do not optimize their own reward. It does not establish that reward maximization *always* harms completion, that bold is always better, or that this test uses independent real-world data. Vary the time budget and slip rate, and compare the proxy with the actual objective. For deployment, independently test task completion and cost/safety constraints on held-out conditions instead of trusting proxy scores alone.

## Sensitivity and replication

The `--stress-test` option runs three illustrative scenarios at 200 paired episodes per scenario with the default seed. These are **not** scientific held-out tests and should not be treated as significance estimates:

| Steps | Slip rate | Cautious goal success | Bold goal success |
|---:|---:|---:|---:|
| 16 | 0.30 | 0.0% | 88.5% |
| 32 | 0.30 | 97.0% | 100.0% |
| 40 | 0.70 | 78.5% | 12.5% |

The last scenario reverses the *actual goal-completion* ranking. Different slip rates and horizons change the task distribution; no matched causal comparison across scenarios is implied. The example's purpose is to reveal proxy sensitivity, not prove which fixed policy is generally better.

All reported values are independently recomputable from `reward_gap.py` and the source-controlled seeds; the updated test suite contains 20 tests, including snapshot metrics, non-finite input rejection and a stress-case regression.
