"""Educational edge-vs-cloud cost model; no hardware measurements performed."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path

HOURS_PER_YEAR = 8760
SECONDS_PER_YEAR = HOURS_PER_YEAR * 3600


@dataclass(frozen=True)
class Scenario:
    items_per_second: float
    device_price: float
    lifespan_years: float
    maintenance_per_year: float
    idle_watts: float
    load_watts: float
    electricity_price_per_kwh: float
    utilization: float
    useful_fraction_edge: float
    cloud_price_per_million_calls: float
    useful_fraction_cloud: float
    currency: str = "USD"

    def validate(self) -> None:
        positive = ("items_per_second", "lifespan_years", "useful_fraction_edge",
                    "useful_fraction_cloud")
        nonnegative = ("device_price", "maintenance_per_year", "idle_watts",
                       "load_watts", "electricity_price_per_kwh",
                       "cloud_price_per_million_calls")
        for name in positive + nonnegative + ("utilization",):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{name} must be a finite number")
            if name in positive and value <= 0:
                raise ValueError(f"{name} must be positive")
            if name in nonnegative and value < 0:
                raise ValueError(f"{name} must be nonnegative")
        for name in ("utilization", "useful_fraction_edge", "useful_fraction_cloud"):
            if getattr(self, name) > 1:
                raise ValueError(f"{name} cannot exceed 1")
        if self.load_watts < self.idle_watts:
            raise ValueError("load_watts must not be below idle_watts")
        if not isinstance(self.currency, str) or not self.currency.strip():
            raise ValueError("currency must be a nonempty label")


def load_scenario(path: str | Path) -> Scenario:
    """Only accepts an explicitly illustrative scenario, never measured claims."""
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("measurement_status") != "illustrative":
        raise ValueError("measurement_status must be 'illustrative'")
    if not isinstance(document.get("assumptions"), dict):
        raise ValueError("assumptions must be a JSON object")
    known = set(Scenario.__dataclass_fields__)
    extras = set(document["assumptions"]) - known
    if extras:
        raise ValueError(f"unknown assumptions: {', '.join(sorted(extras))}")
    try:
        scenario = Scenario(**document["assumptions"])
    except TypeError as exc:
        raise ValueError(f"invalid scenario fields: {exc}") from exc
    scenario.validate()
    return scenario


def estimate(s: Scenario, utilization: float | None = None) -> dict:
    s.validate()
    u = s.utilization if utilization is None else utilization
    if isinstance(u, bool) or not isinstance(u, (int, float)) or not math.isfinite(u) or not 0 <= u <= 1:
        raise ValueError("utilization must be between 0 and 1")

    fixed = (s.device_price / s.lifespan_years + s.maintenance_per_year
             + HOURS_PER_YEAR * s.idle_watts * s.electricity_price_per_kwh / 1000)
    incremental = (HOURS_PER_YEAR * (s.load_watts - s.idle_watts)
                   * s.electricity_price_per_kwh / 1000)
    annual_cost = fixed + incremental * u
    annual_useful_items = s.items_per_second * SECONDS_PER_YEAR * u * s.useful_fraction_edge
    edge_cost = annual_cost * 1_000_000 / annual_useful_items if annual_useful_items else None
    cloud_cost = s.cloud_price_per_million_calls / s.useful_fraction_cloud

    cloud_spend_per_full_utilization = (
        s.items_per_second * SECONDS_PER_YEAR * s.useful_fraction_edge
        * cloud_cost / 1_000_000
    )
    margin = cloud_spend_per_full_utilization - incremental
    threshold = fixed / margin if margin > 0 else None
    if threshold is not None and threshold > 1:
        threshold = None

    values = (annual_cost, annual_useful_items, cloud_cost, margin)
    if any(not math.isfinite(v) for v in values) or (
        edge_cost is not None and not math.isfinite(edge_cost)
    ) or (threshold is not None and not math.isfinite(threshold)):
        raise ValueError("calculation overflow; supply realistic assumptions")

    return {
        "measurement_status": "illustrative_not_measured",
        "currency": s.currency,
        "utilization": u,
        "annual_edge_cost": round(annual_cost, 6),
        "annual_useful_edge_items": round(annual_useful_items, 3),
        "edge_cost_per_million_useful": None if edge_cost is None else round(edge_cost, 6),
        "cloud_cost_per_million_useful": round(cloud_cost, 6),
        "edge_cheaper": None if edge_cost is None else edge_cost < cloud_cost,
        "break_even_utilization": None if threshold is None else round(threshold, 6),
        "limitations": "steady-state, assumption-based; excludes network, cooling, taxes, concurrency and measured quality",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="scenario.json")
    parser.add_argument("--sweep", action="store_true",
                        help="compare assumed utilization levels: 0, 5, 10, 25, 50, 90 percent")
    args = parser.parse_args()
    scenario = load_scenario(args.config)
    levels = (0, 0.05, 0.10, 0.25, 0.50, 0.90) if args.sweep else (scenario.utilization,)
    print(json.dumps([estimate(scenario, u) for u in levels], indent=2))


if __name__ == "__main__":
    main()
