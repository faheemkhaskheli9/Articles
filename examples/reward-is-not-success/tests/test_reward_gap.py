import math
import pytest

from reward_gap import Config, evaluate, evaluate_episode


def test_cautious_cannot_reach_goal_with_sixteen_steps():
    r = evaluate_episode("cautious", (False,) * 16)
    assert r.mean_progress_reward == 1.0
    assert r.goal_reached is False
    assert r.final_distance == pytest.approx(0.36)


def test_bold_success_on_clean_tape():
    r = evaluate_episode("bold", (False,) * 16)
    assert r.goal_reached is True
    assert r.first_hit_step == 8
    assert r.final_distance == 0
    assert r.mean_progress_reward == pytest.approx(8 / 16)


def test_slips_penalize_bold_but_not_cautious():
    tape = (True, False) * 8
    a = evaluate_episode("cautious", tape)
    b = evaluate_episode("bold", tape)
    assert a.mean_progress_reward == 1.0
    assert b.mean_progress_reward < a.mean_progress_reward


def test_fixed_seed_reproduces_report():
    config = Config(episodes=200, seed=42)
    assert evaluate(config) == evaluate(config)


def test_mismatch_is_observable_on_default_config():
    report = evaluate(Config())
    assert report["cautious"]["proxy_reward"] > report["bold"]["proxy_reward"]
    assert report["cautious"]["goal_rate"] < report["bold"]["goal_rate"]


@pytest.mark.parametrize("config", [
    Config(episodes=0), Config(steps=0), Config(goal=0),
    Config(slip_rate=-0.1), Config(slip_rate=1.01),
    Config(slip_rate=float("nan")), Config(slip_rate=float("inf")),
    Config(goal=float("nan")), Config(goal=float("inf")),
])
def test_invalid_configuration_rejected(config):
    with pytest.raises(ValueError):
        evaluate(config)


def test_unknown_policy_and_empty_tape_rejected():
    with pytest.raises(ValueError):
        evaluate_episode("unknown", (False,))
    with pytest.raises(ValueError):
        evaluate_episode("bold", ())


def test_all_slips_has_zero_success():
    report = evaluate(Config(episodes=5, steps=16, slip_rate=1))
    assert report["bold"]["goal_rate"] == 0
    assert report["cautious"]["goal_rate"] == 0


def test_long_horizon_cautious_eventually_succeeds():
    r = evaluate_episode("cautious", (False,) * 30)
    assert r.goal_reached
    assert r.first_hit_step == 25


def test_nonfinite_episode_goal_rejected():
    for invalid in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError):
            evaluate_episode("cautious", (False,) * 16, goal=invalid)


def test_exact_default_snapshot():
    report = evaluate(Config())
    assert report["cautious"]["proxy_reward"] == pytest.approx(1.0)
    assert report["cautious"]["goal_rate"] == pytest.approx(0.0)
    assert report["cautious"]["remaining_distance"] == pytest.approx(0.4545)
    assert report["bold"]["proxy_reward"] == pytest.approx(0.34125)
    assert report["bold"]["goal_rate"] == pytest.approx(0.885)
    assert report["bold"]["remaining_distance"] == pytest.approx(0.0271)


def test_counterexample_stress_condition_reverses_goal_ranking():
    report = evaluate(Config(episodes=200, seed=42, steps=40, slip_rate=0.7))
    assert report["cautious"]["goal_rate"] == pytest.approx(0.785)
    assert report["bold"]["goal_rate"] == pytest.approx(0.125)
    assert report["cautious"]["proxy_reward"] > report["bold"]["proxy_reward"]
