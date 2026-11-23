"""Synthetic recurrent circuit: connectivity alone does not fix dynamics."""
from dataclasses import dataclass
from math import tanh

EDGES = ((0, 1), (1, 2), (2, 1))
STRONG = {(0, 1): 1.5, (1, 2): 2.0, (2, 1): 0.3}
WEAK = {(0, 1): 0.05, (1, 2): 0.08, (2, 1): 0.3}


@dataclass(frozen=True)
class Trace:
    sensory: tuple[float, ...]
    hidden: tuple[float, ...]
    motor: tuple[float, ...]


def simulate(weights: dict[tuple[int, int], float], steps: int = 12,
             stimulus: float = 1.0, leak: float = 0.25) -> Trace:
    """Discrete-time tanh network with fixed topology."""
    if set(weights) != set(EDGES):
        raise ValueError("weights must contain exactly the directed edges")
    if any(v <= 0 for v in weights.values()):
        raise ValueError("weights must all remain positive")
    if steps < 1 or not 0 <= leak < 1:
        raise ValueError("steps and leak are outside valid ranges")
    state = [0.0, 0.0, 0.0]
    series = [[], [], []]
    for _ in range(steps):
        drive = [stimulus, 0.0, 0.0]
        for (start, end), weight in weights.items():
            drive[end] += weight * state[start]
        state = [tanh(drive[i] + leak * state[i]) for i in range(3)]
        for i, value in enumerate(state):
            series[i].append(value)
    return Trace(*(tuple(values) for values in series))


def comparison(steps: int = 12) -> dict[str, object]:
    """Same directed edges and signs; different gains."""
    strong, weak = simulate(STRONG, steps), simulate(WEAK, steps)
    return {
        "edges": [list(edge) for edge in EDGES],
        "same_topology": set(STRONG) == set(WEAK),
        "same_signs": all(STRONG[e] > 0 and WEAK[e] > 0 for e in EDGES),
        "strong_last": strong.motor[-1],
        "weak_last": weak.motor[-1],
        "difference": strong.motor[-1] - weak.motor[-1],
    }
