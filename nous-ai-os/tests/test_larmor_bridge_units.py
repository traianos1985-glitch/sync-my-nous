"""Regression tests for Larmor calculation units and input validation."""
import pytest

from executor.larmor_bridge import calculate_larmor


def test_larmor_frequency_uses_hz_per_tesla() -> None:
    result = calculate_larmor("cu", 0.04823)
    assert "error" not in result
    # 11.3114 MHz/T × 0.04823 T = about 545.4 kHz.
    assert result["f_larmor_hz"] == pytest.approx(545_400, rel=0.002)
    assert result["f_larmor_khz"] == pytest.approx(result["f_larmor_hz"] / 1_000)


@pytest.mark.parametrize("field", [0, -0.048, float("nan"), float("inf"), -float("inf"), None, "not-a-number", True])
def test_larmor_rejects_invalid_magnetic_field(field: object) -> None:
    result = calculate_larmor("cu", field)  # type: ignore[arg-type]
    assert "error" in result
    assert "tesla" in result["error"]


def test_larmor_rejects_unknown_material() -> None:
    result = calculate_larmor("not-a-material", 0.04823)
    assert "error" in result
