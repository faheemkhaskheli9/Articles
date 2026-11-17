"""Math, validation and adversarial tests. All numbers are illustrative."""
import json
import math
from dataclasses import replace

import pytest

from cost_demo import Scenario, estimate, load_scenario


@pytest.fixture
def scenario(tmp_path):
    assumptions = {
        "items_per_second": 8,
        "device_price": 300,
        "lifespan_years": 3,
        "maintenance_per_year": 25,
        "idle_watts": 8,
        "load_watts": 35,
        "electricity_price_per_kwh": .2,
        "utilization": .05,
        "useful_fraction_edge": .95,
        "cloud_price_per_million_calls": 2,
        "useful_fraction_cloud": .95,
    }
    path = tmp_path / "case.json"
    path.write_text(json.dumps({"measurement_status": "illustrative", "assumptions": assumptions}))
    return load_scenario(path)


def test_low_utilization_loses_to_cloud(scenario):
    report = estimate(scenario)
    assert report["edge_cost_per_million_useful"] == pytest.approx(11.797812)
    assert report["cloud_cost_per_million_useful"] == pytest.approx(2.105263)
    assert report["edge_cheaper"] is False


def test_higher_utilization_spreads_fixed_cost(scenario):
    report = estimate(scenario, .5)
    assert report["edge_cost_per_million_useful"] == pytest.approx(1.357413)
    assert report["edge_cheaper"] is True
    assert report["break_even_utilization"] == pytest.approx(.304012)


def test_break_even_equals_cloud_price(scenario):
    threshold = estimate(scenario)["break_even_utilization"]
    report = estimate(scenario, threshold)
    assert report["edge_cost_per_million_useful"] == pytest.approx(
        report["cloud_cost_per_million_useful"], abs=0.00001
    )


def test_zero_utilization_is_not_zero_cost(scenario):
    report = estimate(scenario, 0)
    assert report["annual_edge_cost"] > 0
    assert report["annual_useful_edge_items"] == 0
    assert report["edge_cost_per_million_useful"] is None
    assert report["edge_cheaper"] is None


def test_no_break_even_if_cloud_price_is_free(scenario):
    report = estimate(replace(scenario, cloud_price_per_million_calls=0))
    assert report["break_even_utilization"] is None
    assert report["edge_cheaper"] is False


@pytest.mark.parametrize("changes", [
    {"useful_fraction_edge": 0},
    {"useful_fraction_cloud": 1.1},
    {"idle_watts": 40},
    {"utilization": -0.1},
    {"utilization": True},
    {"items_per_second": float("nan")},
    {"load_watts": float("inf")},
    {"currency": ""},
])
def test_invalid_assumptions_fail_closed(scenario, changes):
    with pytest.raises(ValueError):
        estimate(replace(scenario, **changes))


@pytest.mark.parametrize("override", [float("nan"), float("inf"), -0.01, 1.01, True])
def test_invalid_utilization_override(scenario, override):
    with pytest.raises(ValueError):
        estimate(scenario, override)


def test_unknown_field_is_rejected(tmp_path):
    p = tmp_path / "scenario.json"
    p.write_text(json.dumps({"measurement_status": "illustrative",
                             "assumptions": {"made_up": 1}}))
    with pytest.raises(ValueError, match="unknown assumptions"):
        load_scenario(p)


def test_measurement_provenance_is_never_implied(tmp_path):
    p = tmp_path / "scenario.json"
    p.write_text(json.dumps({"measurement_status": "measured", "assumptions": {}}))
    with pytest.raises(ValueError, match="illustrative"):
        load_scenario(p)
