# My AI Controller Earned More Reward. It Reached Fewer Targets.

*An experiment from my Brain project taught me why a successful AI benchmark can still fail the task that matters. Here is how to reproduce the mistake with Python—and how to evaluate it properly.*

By Faheem Khaskheli · November 17, 2026 · AI Research / Reinforcement Learning / Evaluation

Imagine an AI-controlled robot arm trying to touch a target before a deadline. Every time its hand moves closer, the system earns a point. The score improves. The controller gets better at moving in the right direction.

But it still misses the target.

That is not a hypothetical problem I added to make the introduction interesting. In an experiment in my open-source [Brain project](https://github.com/faheemkhaskheli9/Brain), a controller earned a substantially better *progress reward* while failing to show an improvement in *target contact*. The raw result was uncomfortable enough to change how I think about evaluating AI agents.

The lesson is simple: **a reward function measures the behavior you specified, not necessarily the outcome you wanted.**

This article walks through the original finding, a runnable Python example that isolates the evaluation mistake, and the adversarial checks I would require before calling an AI system better.

## The experiment that exposed the gap

I have been working on sparse, brain-inspired controllers that store small motor-policy checkpoints and select between them using feedback. One research question is whether a controller can adapt when the environment's motor rules change without being told when the change happened.

In the [continuous-body experiment](https://github.com/faheemkhaskheli9/Brain/blob/main/research/continuous-motor-results-2026-11-12.md), I compared a reward-guided policy selector with a periodic-switching baseline. The simulator used a single joint, two previously trained sparse policies, hidden changes in motor direction, noisy feedback, and a **three-action reward delay**. The physical body was not reset when its target or motor rule changed.

The results came from ten reserved simulation seeds, with the experimental protocol committed before those seeds were evaluated.

- **Progress reward per action:** reward-guided controller **+0.2368**, periodic baseline **−0.0531**.
- **Target-contact rate:** reward-guided controller **22.66%**, periodic baseline **25.29%**.
- **Primary reward difference:** +0.28993 per action, with a seed-paired 95% bootstrap interval of **[+0.19981, +0.37557]** and a two-sided exact sign-flip **p = 0.001953125**.
- **Target-contact difference:** **−2.64 percentage points**, with a seed-paired 95% interval of **[−7.37, +1.83] percentage points** and **p = 0.3125**.

The reward improvement passed the preregistered primary test. The apparent decline in target contact **was not statistically conclusive**: the interval includes zero. The defensible statement is not that the new controller was worse at reaching. It is that **better progress reward did not establish better reaching success**.

There is another important boundary: the system did not discover and train new skills during evaluation. Both sparse policies had been trained beforehand, and their weights stayed frozen. The online component selected between saved behaviors. That is *adaptation through policy selection*, not evidence of general intelligence or autonomous skill formation.

The surprising number was not the reward gain. It was the failure of that gain to transfer cleanly to the user-visible objective.

## Why moving closer is not the same as arriving

Suppose the objective is to touch a target within 16 actions. A developer chooses a dense reward:

- +1 when the distance to the target decreases.
- −1 when it increases.
- 0 when it stays unchanged.

This makes sense. The signal is available more often than a rare success event, and it can help a learning system identify useful directions.

But it rewards a *step*, not a *completed task*. A policy that moves forward a tiny amount on every step can collect consistently positive feedback without ever arriving before the deadline. Another policy may risk occasional backward steps and receive a lower progress score while actually reaching the target.

This is a form of **proxy-objective mismatch**. In a trained system, optimizing the proxy can produce specification gaming. [Concrete Problems in AI Safety](https://arxiv.org/abs/1606.06565) identified reward hacking as a practical failure mode; [DeepMind's specification-gaming examples](https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/) show how systems satisfy a reward specification without fulfilling the developer's intention. The ICLR 2024 paper [Goodhart's Law in Reinforcement Learning](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6ad68a54eaa8f9bf6ac698b02ec05048-Abstract-Conference.html) evaluates related proxy-reward failures experimentally.

The Brain result does **not** prove that its controller learned to game the reward. It shows an evaluation mismatch: reward and task success pointed in different directions, and only one difference was statistically supported.

## A runnable example: two policies, one goal

I built a small [Python companion project](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/reward-is-not-success) to make the distinction visible without requiring a GPU, an LLM API, or even NumPy.

The environment is deliberately simple. An agent starts at position 0 and must reach position 1 within 16 steps. Each step may experience a simulated slip. Two fixed, handcrafted policies receive the same slip sequence in each paired episode:

1. **Cautious:** moves +0.04 on normal steps or +0.02 on slips. It never takes a backward step, so its progress reward looks excellent. But even 16 perfect steps cover only 0.64 of the required distance.
2. **Bold:** moves +0.14 on normal steps or −0.06 on slips. It can lose progress and reward, but it also has a chance of finishing within the deadline.

The evaluator keeps three outputs separate: mean progress reward, fraction of episodes in which the goal was actually reached, and remaining distance at the deadline. Once a policy reaches the goal, the remaining action slots receive zero progress reward; both policies use the same 16-slot evaluation horizon.

You can inspect the complete implementation in [`reward_gap.py`](https://github.com/faheemkhaskheli9/Articles/blob/main/examples/reward-is-not-success/reward_gap.py), plus its tests and VS Code launch configuration.

Run it with Python 3.10 or newer:

```bash
git clone https://github.com/faheemkhaskheli9/Articles.git
cd Articles/examples/reward-is-not-success
python -m pip install -r requirements.txt
python reward_gap.py --episodes 200 --seed 42 --steps 16 --slip-rate 0.30
python -m pytest -q
```

Here is the output from that exact deterministic configuration:

```text
policy     proxy_reward  goal_rate  remaining_distance
cautious          1.000       0.0%               0.455
bold              0.341      88.5%               0.027
```

If I ranked the policies by progress reward alone, cautious would win decisively. If I ranked them by whether they accomplished the task, bold would win. **The ranking reverses because the metrics answer different questions.**

This is an intentionally constructed teaching example with two fixed policies. No model learned or deliberately exploited the reward. Its numbers must **not** be described as new results from the Brain experiment or as a scientific benchmark of learning algorithms. The simulation demonstrates that this failure is possible, not how frequently it occurs in production.

## The evaluation protocol I would use instead

A useful AI evaluation must describe success independently of the signal being optimized. For a controller, agent, or LLM workflow, I would define five things before running the comparison.

1. **Primary user outcome.** For the robot: did it touch the target within the deadline? For a support agent: was the customer's issue actually resolved? This must not be replaced by a model's own confidence score.
2. **Proxy diagnostic.** Measure progress reward, policy-selection accuracy, tool-call validity, or other intermediate signals—but keep them visibly separate from completion.
3. **Action and time budget.** Count attempts, steps, latency, retries, and side effects. A system that eventually succeeds after ten times the work may not be an improvement.
4. **Fair comparison.** Freeze the evaluation protocol, use comparable task instances and budgets, retain failures, and compare results across independent seeds or tasks. In the Brain experiment, the ten seeds—not the thousands of individual action steps—were the paired statistical units.
5. **Failure-triggering conditions.** Test delayed feedback, noisy observations, unseen changes, and environments for which no stored policy works. Report what happens when the controller has no valid answer.

I would also track final distance, stable target contact, false policy switches, and recovery time. In a customer-facing LLM agent, the analogous outputs are final business state, unauthorized side effects, retries, and independently verified task success.

**Important:** a single weighted score is not a substitute for this breakdown. Weighting success, progress, and latency together can hide a severe failure in one dimension behind an improvement in another.

## The adversarial review

Before treating the result as proof of a better AI controller, I tried to identify the strongest reasons it might be misleading.

**First: a statistical win on one metric is not a win on every metric.** The Brain experiment's reward comparison was preregistered and significant within the toy simulator. The target-contact comparison was inconclusive. Reporting only the first result would overstate the conclusion; reporting the second as a confirmed regression would also overstate it.

**Second: the controller already knew both kinds of behavior.** It switched among two pretrained checkpoints. A hidden third motor regime with no compatible checkpoint might defeat it entirely. That is a necessary stress test for future experiments, not a capability the existing result establishes.

**Third: the reward function was engineered to be informative.** The simulator exposed signed target error and a simple ±1 progress signal. Natural environments have ambiguous goals, sparse feedback, sensory uncertainty, and consequences that appear much later. The result cannot be transferred directly to a physical robot, much less a human brain.

**Fourth: the Python demonstration is intentionally favorable to a ranking reversal.** Cautious cannot cross the finish line in 16 steps by construction. That cleanly explains the logical problem but does not estimate any real-world effect size. Longer deadlines, different slip rates, a terminal success reward, or a different task can change the result. Run the alternatives instead of generalizing the one output.

**Fifth: paired seeds reduce noise, not every confound.** The Brain controllers operated on different physical trajectories because each chose different actions. Equal starting seeds and noise tapes cannot make those trajectories identical. The appropriate interpretation is an observed policy-level comparison under a controlled simulated protocol, not a claim about all counterfactual actions.

A good adversarial review should not erase a positive finding. It should define exactly what survives the criticism. Here the positive finding is **reward-driven selection improved the measured progress signal under the frozen test conditions**. The unresolved question is whether that mechanism consistently improves actual task completion.

## What this changes in my AI projects

The same mistake is easy to make outside reinforcement learning.

A multilingual AI agent can select the right tool while filling the wrong amount. A RAG system can return a citation while misrepresenting what the source says. A text-to-SQL model can generate authorized SQL that computes the wrong revenue. And a robot can move toward a target without ever reaching it.

In each case, an intermediate check passed. The intended outcome did not follow automatically. That is why the rest of my work on [Sindhi-AgentBench](https://github.com/faheemkhaskheli9/Sindhi-AgentBench), [LLM evaluation examples](https://github.com/faheemkhaskheli9/Articles), and the [Brain experiments](https://github.com/faheemkhaskheli9/Brain) separates action validity, measured intermediate performance, and independently verifiable completion.

The next Brain experiment should make actual goal contact a primary decision gate, not merely an interesting secondary column. It also needs a fresh held-out seed set, an unseen motor regime, and metrics for action cost and stable contact. Reusing the already observed test seeds to tune the reward would undermine the evidence.

## Try the failure yourself

The [companion repository](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/reward-is-not-success) includes the entire offline experiment, dependency file, `.env.example`, VS Code launch configurations, and automated tests. Change `--slip-rate` or `--steps`; keep the same seed for a controlled comparison, then run new seeds to test robustness.

If there is one question worth adding to every agent evaluation dashboard, it is not just "Did the score improve?"

It is **"Did the user-visible task improve too?"**

## References

1. Brain research: [Continuous toy-body context switching under delayed reward: ten-seed result](https://github.com/faheemkhaskheli9/Brain/blob/main/research/continuous-motor-results-2026-11-12.md), with preregistered protocol and auditable raw results.
2. Amodei et al., [Concrete Problems in AI Safety](https://arxiv.org/abs/1606.06565) (2016).
3. Google DeepMind, [Specification gaming: the flip side of AI ingenuity](https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/) (2020).
4. Karwowski et al., [Goodhart's Law in Reinforcement Learning](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6ad68a54eaa8f9bf6ac698b02ec05048-Abstract-Conference.html), ICLR 2024.
5. Source code: [Reward is not success — executable example and tests](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/reward-is-not-success).
