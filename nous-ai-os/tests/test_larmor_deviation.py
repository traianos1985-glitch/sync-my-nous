"""Parity and route tests for executor/larmor_deviation.py.

The golden outputs in fixtures/larmor_deviation_golden.json were produced by the
JavaScript model (OpenKBS functions/api/lib/deviation.mjs, with listCalibrations
returning executor/larmor_calibrations.json and wave() from research-assistant.mjs)
under Node 24 for every case's ``args``. Regenerate them the same way whenever the
model or the calibration file changes.
"""

import json
import re
from pathlib import Path

import pytest

from executor import larmor_deviation
from executor.larmor_deviation import field_deviation

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "larmor_deviation_golden.json").read_text(encoding="utf-8"))


def _assert_same(got, expected, path="$"):
    if isinstance(expected, dict):
        assert isinstance(got, dict), path
        assert list(got) == list(expected), f"{path}: keys differ"
        for key in expected:
            _assert_same(got[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(got, list) and len(got) == len(expected), path
        for i, (g, e) in enumerate(zip(got, expected, strict=True)):
            _assert_same(g, e, f"{path}[{i}]")
    elif isinstance(expected, bool) or expected is None or isinstance(expected, str):
        assert got == expected and type(got) is type(expected), f"{path}: {got!r} != {expected!r}"
    else:
        # Rounded outputs match exactly; unrounded internals may differ in the last bit (libm vs V8).
        assert isinstance(got, (int, float)) and not isinstance(got, bool), path
        assert got == pytest.approx(expected, rel=1e-12, abs=1e-15), f"{path}: {got!r} != {expected!r}"


@pytest.mark.parametrize("name", sorted(GOLDEN))
def test_matches_javascript_model(name):
    case = GOLDEN[name]
    _assert_same(field_deviation(json.loads(json.dumps(case["args"]))), case["expected"])


def test_golden_cases_cover_every_mode():
    expected = {name: case["expected"] for name, case in GOLDEN.items()}
    assert expected["exact_1ghz_coins_gps"]["calibration_used"]["method"] == "μετρημένη συχνότητα"
    assert "estimated_target" in expected["exact_1ghz_coins_gps"]["prediction"]
    assert expected["interpolated_2ghz_mn"]["calibration_used"]["method"].startswith("παρεμβολή")
    assert expected["out_of_range_low"]["calibration_used"]["method"].startswith("εκτός εύρους")
    assert expected["out_of_range_high"]["calibration_used"]["method"].startswith("εκτός εύρους")
    assert "channel_note" in expected["unknown_channel_fallback"]["calibration_used"]
    assert set(expected["spacing_only"]) == {"ok", "stake_spacing"}
    assert "east_m" in expected["tri_local_3"]["combined_target"]
    assert "lat" in expected["tri_gps_3"]["combined_target"]
    outlier = expected["tri_local_4_one_outlier"]
    assert [p["agrees"] for p in outlier["points"]] == [True, True, True, False]
    assert outlier["combined_without_outliers"]["frequencies"] == ["1 GHz", "3 GHz", "6 GHz"]
    assert "combined_without_outliers" not in expected["tri_local_3_all_disagree"]
    assert len(expected["tri_seven_points_truncated"]["points"]) == larmor_deviation.MAX_TRI_POINTS
    errors = {name: e["error"] for name, e in expected.items() if not e["ok"]}
    assert errors["error_point_bad_frequency"] == "frequency_hz_required"
    assert "point" in expected["error_point_bad_frequency"]


def test_json_output_is_text_identical_for_rounded_results():
    case = GOLDEN["tri_local_4_one_outlier"]
    got = field_deviation(case["args"])
    assert json.dumps(got, ensure_ascii=False, sort_keys=True) == json.dumps(
        case["expected"], ensure_ascii=False, sort_keys=True
    )


def test_burial_year_is_converted_to_years_buried():
    out = field_deviation({"frequency_hz": 1e9, "burial_year": 1950})
    now = larmor_deviation._now_year()
    assert out["ok"] is True
    assert out["input"]["years_buried"] == pytest.approx(now - 1950, rel=1e-2)
    future = field_deviation({"frequency_hz": 1e9, "burial_year": 3000})
    assert future["input"]["years_buried"] == 0


def test_javascript_rounding_semantics():
    assert larmor_deviation.round_js(0.125, 2) == 0.13  # toPrecision rounds ties away from zero
    assert larmor_deviation.round_js(-0.125, 2) == -0.13
    assert larmor_deviation.round_js(float("nan")) is None
    assert larmor_deviation._to_fixed(1.005) == "1.00"  # exact binary value is below the tie
    assert larmor_deviation._to_fixed(0.125) == "0.13"
    assert larmor_deviation._math_round(-2.5) == -2
    assert larmor_deviation._js_num_str(1e21) == "1e+21"
    assert larmor_deviation._js_num_str(1e-7) == "1e-7"
    assert larmor_deviation._js_num_str(2.5) == "2.5"


@pytest.mark.parametrize("bad", [None, [], "text", 3])
def test_non_dict_arguments_are_rejected(bad):
    assert field_deviation(bad) == {"ok": False, "error": "invalid_arguments"}


def test_output_is_strict_json():
    out = field_deviation({"frequency_hz": 1e9, "target_depth_m": 0, "box_height_m": 0, "box_length_m": 0})
    json.dumps(out, allow_nan=False)


def test_calibration_file_is_read_only_data_without_locations():
    raw = larmor_deviation.CALIBRATIONS_PATH.read_text(encoding="utf-8")
    records = json.loads(raw)["records"]
    allowed = {
        "session",
        "channel",
        "frequency_hz",
        "distance_m",
        "bearing_deg",
        "generator_bearing_deg",
        "target",
        "target_depth_m",
        "years_buried",
        "stake_spacing_m",
        "notes",
    }
    assert len(records) == 15
    assert all(set(r) == allowed for r in records)
    values = json.dumps(records, ensure_ascii=False)
    assert not re.search(r"\b(lat|lon|lng|gps|coord)", values, re.IGNORECASE)
    assert not re.search(r"-?\d{1,3}\.\d{4,}", values)  # nothing that looks like a decimal coordinate
    assert {r["session"] for r in records} == {"session 5", "session 6"}


# ---------------------------------------------------------------------------
# Route


def _master_header(monkeypatch):
    token = "larmor-deviation-route-master-token"
    monkeypatch.setenv("NOUS_TOKEN", token)
    return {"Authorization": f"Bearer {token}"}


def test_deviation_route_requires_token(monkeypatch):
    pytest.importorskip("flask")
    from executor import router

    _master_header(monkeypatch)
    response = router.app.test_client().post("/larmor/deviation", json={"frequency_hz": 1e9})
    assert response.status_code == 401


def test_deviation_route_requires_admin_scope(monkeypatch):
    pytest.importorskip("flask")
    from executor import router

    headers = _master_header(monkeypatch)
    monkeypatch.setattr(router, "check_admin_token", lambda _request: False)
    response = router.app.test_client().post("/larmor/deviation", json={"frequency_hz": 1e9}, headers=headers)
    assert response.status_code == 401
    assert response.get_json() == {"error": "unauthorized"}


def test_deviation_route_returns_model_output_for_admin(monkeypatch):
    pytest.importorskip("flask")
    from executor import router

    headers = _master_header(monkeypatch)
    client = router.app.test_client()
    case = GOLDEN["tri_local_3"]
    response = client.post("/larmor/deviation", json=case["args"], headers=headers)
    assert response.status_code == 200
    _assert_same(response.get_json(), json.loads(json.dumps(case["expected"], sort_keys=True)))

    invalid = client.post("/larmor/deviation", json={"frequency_hz": -1}, headers=headers)
    assert invalid.status_code == 200
    assert invalid.get_json() == {"ok": False, "error": "frequency_hz_required"}

    not_object = client.post("/larmor/deviation", json=[1, 2], headers=headers)
    assert not_object.status_code == 400
    assert not_object.get_json()["ok"] is False
