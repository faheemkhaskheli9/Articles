"""Reproducible toy example: proxy reward can disagree with goal completion.

This is an educational simulation, NOT a reproduction of the Brain controller.
Each paired episode uses an identical pre-sampled slip sequence for both policies.
No policies are trained, and the event tape never depends on the chosen policy.
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
import math
from statistics import mean


@dataclass(frozen=True)
class Config:
    episodes: int = 200
    seed: int = 42
    steps: int = 16
    slip_rate: float = 0.30
    goal: float = 1.0

    def validate(self) -> None:
        if self.episodes <= 0 or self.steps <= 0 or not math.isfinite(self.goal) or self.goal <= 0:
            raise ValueError("episodes, steps, and goal must be positive")
        if not math.isfinite(self.slip_rate) or not 0 <= self.slip_rate <= 1:
            raise ValueError("slip_rate must be between 0 and 1")


@dataclass(frozen=True)
class Outcome:
    mean_progress_reward: float
    goal_reached: bool
    final_distance: float
    first_hit_step: int | None


def evaluate_episode(policy: str, slips: tuple[bool, ...], goal: float = 1.0) -> Outcome:
    """Both arms receive the SAME slips; reward is sign of distance improvement.

    After goal contact the remaining time slots count as zero proxy reward;
    the fixed horizon is identical for every policy and episode.
    """
    if policy not in {"cautious", "bold"}:
        raise ValueError(f"unknown policy: {policy}")
    if not slips or not math.isfinite(goal) or goal <= 0:
        raise ValueError("slips must be nonempty and goal positive")
    position = 0.0
    total_reward = 0.0
    hit_step: int | None = None
    for step, slip in enumerate(slips, start=1):
        if hit_step is not None:
            continue
        if policy == "cautious":
            displacement = 0.02 if slip else 0.04
        else:
            displacement = -0.06 if slip else 0.14
        before = abs(goal - position)
        position = max(0.0, min(goal, position + displacement))
        after = abs(goal - position)
        if after < before:
            total_reward += 1.0
        elif after > before:
            total_reward -= 1.0
        if position >= goal:
            hit_step = step
    return Outcome(
        mean_progress_reward=total_reward / len(slips),
        goal_reached=hit_step is not None,
        final_distance=goal - position,
        first_hit_step=hit_step,
    )


def evaluate(config: Config) -> dict[str, dict[str, float]]:
    config.validate()
    rng = random.Random(config.seed)
    rows: dict[str, list[Outcome]] = {"cautious": [], "bold": []}
    for _ in range(config.episodes):
        tape = tuple(rng.random() < config.slip_rate for _ in range(config.steps))
        for policy in rows:
            rows[policy].append(evaluate_episode(policy, tape, config.goal))
    return {
        policy: {
            "proxy_reward": mean(o.mean_progress_reward for o in outcomes),
            "goal_rate": mean(float(o.goal_reached) for o in outcomes),
            "remaining_distance": mean(o.final_distance for o in outcomes),
            "episodes": float(len(outcomes)),
        }
        for policy, outcomes in rows.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=16)
    parser.add_argument("--slip-rate", type=float, default=0.30)
    parser.add_argument("--stress-test", action="store_true", help="show how the rankings change across three illustrative conditions")
    args = parser.parse_args()
    if args.stress_test:
        for steps, slip_rate in ((16, 0.30), (32, 0.30), (40, 0.70)):
            rows = evaluate(Config(args.episodes, args.seed, steps, slip_rate))
            a, b = rows["cautious"], rows["bold"]
            print(f"steps={steps:2}, slip={slip_rate:.2f}: "
                  f"cautious goal={a['goal_rate']:.1%}, bold goal={b['goal_rate']:.1%}; "
                  f"cautious reward={a['proxy_reward']:.3f}, bold reward={b['proxy_reward']:.3f}")
        return
    config = Config(args.episodes, args.seed, args.steps, args.slip_rate)
    report = evaluate(config)
    print(f"Paired episodes={config.episodes}, seed={config.seed}, steps={config.steps}, slip_rate={config.slip_rate:.2f}")
    print("policy     proxy_reward  goal_rate  remaining_distance")
    for policy, values in report.items():
        print(f"{policy:<11}{values['proxy_reward']:>12.3f}{values['goal_rate']:>11.1%}{values['remaining_distance']:>20.3f}")
    print("The proxy is signed movement toward the goal, not task completion.")
    print("These fixed handcrafted policies are not trained models or a real-world benchmark.")


if __name__ == "__main__":
    main()
