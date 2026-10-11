"""Regression tests for the classical-EM skin-depth calculations."""
import math

import pytest

from executor.larmor_bridge import (
    METAL_EM_PROPERTIES,
    _MU0,
    characteristic_frequency_hz,
    optimal_em_frequency_hz,
    skin_depth_in_metal_m,
)


def test_characteristic_frequency_matches_skin_depth_radius_crossover() -> None:
    sigma = METAL_EM_PROPERTIES["cu"]["sigma"]
    mu_r = METAL_EM_PROPERTIES["cu"]["mu_r"]
    radius_m = 0.03
    frequency = characteristic_frequency_hz(sigma, mu_r, radius_m)
    assert frequency == pytest.approx(1 / (math.pi * sigma * _MU0 * mu_r * radius_m**2))
    assert skin_depth_in_metal_m(sigma, mu_r, frequency) == pytest.approx(radius_m, rel=0.002)


def test_age_factor_changes_soil_limit_and_is_reported() -> None:
    recent = optimal_em_frequency_hz("cu", 0.03, 1.0, 0.01, age_factor=1.0)
    older = optimal_em_frequency_hz("cu", 0.03, 1.0, 0.01, age_factor=2.0)
    assert "error" not in recent
    assert "error" not in older
    assert older["f_soil_limit_hz"] == pytest.approx(recent["f_soil_limit_hz"] / 4)
    assert older["age_factor"] == 2.0
    assert older["f_optimal_hz"] == older["f_char_hz"]
    assert "not a validated" in older["model_note"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"radius_m": 0},
        {"depth_m": -1},
        {"soil_sigma": float("nan")},
        {"age_factor": float("inf")},
    ],
)
def test_optimal_em_rejects_invalid_numeric_inputs(kwargs: dict[str, float]) -> None:
    values = {"radius_m": 0.03, "depth_m": 1.0, "soil_sigma": 0.01, "age_factor": 1.0}
    values.update(kwargs)
    result = optimal_em_frequency_hz("cu", **values)
    assert "error" in result
