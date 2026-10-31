"""Deviation model for the Larmor field method (read-only port of OpenKBS ``lib/deviation.mjs``).

How far from the final point of the rods the buried target probably is, for a
chosen generator frequency. It starts from calibration records (the rods'
final point around a target whose position is known; session 5 = empty ammo
box 3 cm deep, 3 years buried) and transfers them to another target (depth,
size, contents, burial year) under three competing hypotheses:

  A  geometry: the offset is set by generator position and frequency; the
     target only triggers the response, so the offset stays as calibrated.
  B  oblique projection: the response follows field lines that reach the
     target at an angle, so a deeper target shifts the point by dz*tan(theta).
  C  target strength: a weaker surface anomaly (deeper, smaller) lets the
     setup's own field pattern dominate, so the offset grows.

The spread between them, the calibration spread and the target's own size make
the search radius. Every scaling is a hypothesis and is labelled so.

This module is pure and read-only: calibration records come from the static
``larmor_calibrations.json`` next to it and nothing is ever written. Numbers
follow JavaScript semantics (``toPrecision``/``toFixed`` rounding, NaN/Infinity
instead of exceptions, ``null`` for non-finite values) so the JSON output
matches the JavaScript implementation.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path

CALIBRATIONS_PATH = Path(__file__).with_name("larmor_calibrations.json")

DEG = math.pi / 180
EARTH_R = 6_371_000
NAN = float("nan")
INF = float("inf")

# Without repeats the calibration spread is unknown; assume this much.
DEFAULT_REL_SPREAD = 0.35
DEFAULT_BEARING_SPREAD = 20
WEIGHTS = {"A": 0.4, "B": 0.35, "C": 0.25}
# Corrosion/oxide halo around buried steel, growing like diffusion: r = k*sqrt(t) (hypothesis).
HALO_M_PER_SQRT_YEAR = 0.02
HALO_MAX_M = 0.3
# .30/.50-cal ammo box, roughly 28 x 18 x 10 cm (outer).
AMMO_BOX = {"length_m": 0.28, "width_m": 0.18, "height_m": 0.1}
SOVEREIGN = {"mass_g": 7.988, "gold_g": 7.322, "diameter_mm": 22.05, "thickness_mm": 1.52}
SOILS = {
    "dry": {"permittivity": 4, "conductivity": 0.001},
    "medium": {"permittivity": 10, "conductivity": 0.01},
    "wet": {"permittivity": 25, "conductivity": 0.05},
}

# Plane-wave constants (research-assistant.mjs).
C_LIGHT = 299_792_458
MU0 = 4e-7 * math.pi
EPS0 = 1 / (MU0 * C_LIGHT * C_LIGHT)

_MISSING = object()  # JavaScript `undefined` (absent property), distinct from JSON null.


# ---------------------------------------------------------------------------
# JavaScript number semantics


def _finite(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


_JS_DECIMAL = re.compile(r"[+-]?(?:\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)")


def _js_number(v) -> float:
    """``Number(v)``."""
    if v is _MISSING:
        return NAN
    if v is None:
        return 0.0
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        try:
            return float(v)
        except OverflowError:
            return INF if v > 0 else -INF
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return 0.0
        if s in ("Infinity", "+Infinity"):
            return INF
        if s == "-Infinity":
            return -INF
        for prefix, base in (("0x", 16), ("0o", 8), ("0b", 2)):
            if s[:2].lower() == prefix:
                try:
                    return float(int(s[2:], base)) if s[2:].isalnum() else NAN
                except (ValueError, OverflowError):
                    return NAN
        if _JS_DECIMAL.fullmatch(s):
            return float(s)
        return NAN
    if isinstance(v, list):
        if not v:
            return 0.0
        if len(v) == 1:
            return 0.0 if v[0] is None else _js_number(_js_string(v[0]))
        return NAN
    return NAN


def _nullish(v) -> bool:
    return v is None or v is _MISSING


def num(v, d):
    """``num`` of deviation.mjs: a finite number, else the default."""
    if _nullish(v) or (isinstance(v, str) and v == ""):
        return d
    n = _js_number(v)
    return n if math.isfinite(n) else d


def _js_truthy(v) -> bool:
    if _nullish(v) or v is False:
        return False
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return not (v == 0 or math.isnan(v))
    if isinstance(v, str):
        return v != ""
    return True


def _js_num_str(x) -> str:
    """``String(number)``."""
    x = float(x)
    if math.isnan(x):
        return "NaN"
    if math.isinf(x):
        return "Infinity" if x > 0 else "-Infinity"
    if x == 0:
        return "0"
    sign = "-" if x < 0 else ""
    d = Decimal(repr(abs(x))).normalize()
    _, digit_tuple, exponent = d.as_tuple()
    digits = "".join(map(str, digit_tuple))
    k = len(digits)
    n = exponent + k
    if k <= n <= 21:
        body = digits + "0" * (n - k)
    elif 0 < n <= 21:
        body = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        body = "0." + "0" * (-n) + digits
    else:
        e = n - 1
        mantissa = digits if k == 1 else digits[0] + "." + digits[1:]
        body = f"{mantissa}e{'+' if e >= 0 else '-'}{abs(e)}"
    return sign + body


def _js_string(v) -> str:
    """``String(v)`` / template-literal interpolation."""
    if isinstance(v, str):
        return v
    if v is None:
        return "null"
    if v is _MISSING:
        return "undefined"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return _js_num_str(v)
    if isinstance(v, list):
        return ",".join("" if item is None else _js_string(item) for item in v)
    return "[object Object]"


def _to_precision(v: float, digits: int) -> float:
    """``Number(v.toPrecision(digits))`` (round half away from zero on the exact binary value)."""
    if v == 0:
        return 0.0
    d = Decimal(float(v))
    quantum = Decimal(1).scaleb(d.adjusted() - digits + 1)
    return float(d.quantize(quantum, rounding=ROUND_HALF_UP))


def round_js(v, digits: int = 3):
    """``round`` of deviation.mjs: toPrecision, ``None`` (JSON null) when not finite."""
    if not _finite(v):
        return None
    return _to_precision(v, digits)


def _round_wave(v, digits: int = 4):
    """``round`` of research-assistant.mjs (no finiteness check)."""
    return _to_precision(v, digits) if _finite(v) else float(v)


def _to_fixed(x, digits: int = 2) -> str:
    """``x.toFixed(digits)``."""
    if not _finite(x) or abs(x) >= 1e21:
        return _js_string(x)
    if x == 0:
        x = 0.0
    return format(Decimal(float(x)).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP), "f")


def _math_round(x: float) -> float:
    """``Math.round``: nearest integer, ties toward +Infinity."""
    if not math.isfinite(x):
        return x
    r = math.floor(x)
    return float(r + 1 if x - r >= 0.5 else r)


def _div(a: float, b: float) -> float:
    try:
        return a / b
    except ZeroDivisionError:
        if a == 0 or math.isnan(a):
            return NAN
        return math.copysign(INF, a) * math.copysign(1.0, b)


def _pow(a: float, b: float) -> float:
    try:
        return math.pow(a, b)
    except ValueError:
        return INF if a == 0 else NAN
    except OverflowError:
        odd = float(b).is_integer() and int(b) % 2 == 1
        return -INF if a < 0 and odd else INF


def _sqrt(x: float) -> float:
    return math.sqrt(x) if x >= 0 else NAN


def _log10(x: float) -> float:
    if x > 0:
        return math.log10(x)
    return -INF if x == 0 else NAN


def _sin(x: float) -> float:
    return math.sin(x) if math.isfinite(x) else NAN


def _cos(x: float) -> float:
    return math.cos(x) if math.isfinite(x) else NAN


def _tan(x: float) -> float:
    return math.tan(x) if math.isfinite(x) else NAN


def _asin(x: float) -> float:
    return math.asin(x) if -1 <= x <= 1 else NAN


def _cbrt(x: float) -> float:
    if hasattr(math, "cbrt"):
        return math.cbrt(x)
    return math.copysign(abs(x) ** (1 / 3), x)  # pragma: no cover - Python < 3.11


def _min(*xs: float) -> float:
    return NAN if any(math.isnan(x) for x in xs) else min(xs)


def _max(*xs: float) -> float:
    return NAN if any(math.isnan(x) for x in xs) else max(xs)


def _jsmod(a: float, b: float) -> float:
    return math.fmod(a, b) if math.isfinite(a) else NAN


def norm(deg: float) -> float:
    return _jsmod(_jsmod(deg, 360) + 360, 360)


def angle_diff(a: float, b: float) -> float:
    return _jsmod(b - a + 540, 360) - 180


def _prop(obj, key):
    """``obj.key`` with ``undefined`` for absent properties."""
    return obj.get(key, _MISSING) if isinstance(obj, dict) else _MISSING


def _coalesce(v, d):
    """``v ?? d``."""
    return d if _nullish(v) else v


def _json_ready(value):
    """Mirror JSON.stringify: non-finite numbers -> null, integral numbers without a fraction."""
    if isinstance(value, dict):
        return {k: _json_ready(v) for k, v in value.items() if v is not _MISSING}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        if value.is_integer() and abs(value) < 1e21:
            return int(value)
    return value


# ---------------------------------------------------------------------------
# Physics helpers


def wave(f: float, er: float, sigma: float) -> dict:
    """Plane wave in a lossy half-space with constant sigma and er (no water relaxation)."""
    w = 2 * math.pi * f
    p = sigma / (w * EPS0 * er)
    k = w * math.sqrt(MU0 * EPS0 * er)
    alpha = k * math.sqrt((math.sqrt(1 + p * p) - 1) / 2)
    beta = k * math.sqrt((math.sqrt(1 + p * p) + 1) / 2)
    if p > 10:
        regime = "αγώγιμο (διάχυση, ρεύματα αγωγιμότητας)"
    elif p < 0.1:
        regime = "διηλεκτρικό (κύμα)"
    else:
        regime = "μεταβατικό"
    return {
        "frequency_hz": f,
        "loss_tangent": _round_wave(p, 3),
        "regime": regime,
        "corner_frequency_hz": _round_wave(sigma / (2 * math.pi * EPS0 * er), 4),
        "wavelength_in_soil_m": _round_wave(_div(2 * math.pi, beta)),
        "wavelength_in_air_m": _round_wave(C_LIGHT / f),
        "near_field_radius_air_m": _round_wave(C_LIGHT / f / (2 * math.pi)),
        "penetration_1_over_e_m": _round_wave(_div(1, alpha)),
        "attenuation_db_per_m": _round_wave(8.686 * alpha, 3),
        "standing_wave_spacing_air_m": _round_wave(C_LIGHT / f / 2),
    }


def fmt_hz(f: float) -> str:
    if f >= 1e9:
        return f"{_js_string(round_js(f / 1e9, 4))} GHz"
    if f >= 1e6:
        return f"{_js_string(round_js(f / 1e6, 4))} MHz"
    if f >= 1e3:
        return f"{_js_string(round_js(f / 1e3, 4))} kHz"
    return f"{_js_string(round_js(f, 4))} Hz"


# ---------------------------------------------------------------------------
# Calibration records (read-only)


@lru_cache(maxsize=1)
def _load_calibrations() -> tuple:
    with CALIBRATIONS_PATH.open(encoding="utf-8") as fh:
        records = json.load(fh)["records"]
    return tuple(records)


def list_calibrations() -> list[dict]:
    """All calibration records, ordered by channel, frequency (nulls first), recording order."""
    return [dict(r, id=str(i + 1)) for i, r in enumerate(_load_calibrations())]


def group_by_frequency(records: list[dict]) -> list[dict]:
    """Repeats at one frequency -> mean distance, circular mean bearing (relative to the generator) and spread."""
    groups: dict[float, list[dict]] = {}
    for r in records:
        if _nullish(r.get("frequency_hz")) or _nullish(r.get("bearing_deg")):
            continue
        groups.setdefault(r["frequency_hz"], []).append(r)
    out = []
    for f, rs in groups.items():
        ds = [r["distance_m"] for r in rs]
        rel = [norm(r["bearing_deg"] - r["generator_bearing_deg"]) for r in rs]
        total = 0
        for x in ds:
            total += x
        mean = total / len(ds)
        sin_sum = 0
        cos_sum = 0
        for x in rel:
            sin_sum += math.sin(x * DEG)
        for x in rel:
            cos_sum += math.cos(x * DEG)
        bearing = norm(math.atan2(sin_sum, cos_sum) / DEG)
        sd = None
        if len(ds) > 1:
            sq = 0
            for x in ds:
                sq += (x - mean) ** 2
            sd = math.sqrt(sq / (len(ds) - 1))
        bsd = None
        if len(rel) > 1:
            sq = 0
            for x in rel:
                sq += angle_diff(bearing, x) ** 2
            bsd = math.sqrt(sq / (len(rel) - 1))
        depth_sum = 0
        years_sum = 0
        for r in rs:
            depth_sum += r["target_depth_m"]
        for r in rs:
            years_sum += r["years_buried"]
        spacing = next((r["stake_spacing_m"] for r in rs if not _nullish(r.get("stake_spacing_m"))), None)
        out.append(
            {
                "frequency_hz": f,
                "n": len(rs),
                "distance_m": mean,
                "relative_bearing_deg": bearing,
                "distance_sd_m": sd if sd is not None else mean * DEFAULT_REL_SPREAD,
                "bearing_sd_deg": bsd if bsd is not None else DEFAULT_BEARING_SPREAD,
                "spread_measured": len(ds) > 1,
                "depth_m": depth_sum / len(rs),
                "years": years_sum / len(rs),
                "spacing_m": spacing,
                "sessions": list(dict.fromkeys(r["session"] for r in rs)),
            }
        )
    out.sort(key=lambda p: p["frequency_hz"])
    return out


def interpolate(points: list[dict], f: float) -> dict:
    """Linear in log(f) between the neighbouring calibrated frequencies; outside the range the nearest point."""
    exact = next((p for p in points if abs(math.log10(p["frequency_hz"] / f)) < 0.005), None)
    if exact is not None:
        return dict(exact, method="μετρημένη συχνότητα", extrapolated=False)
    lower = next((p for p in reversed(points) if p["frequency_hz"] < f), None)
    upper = next((p for p in points if p["frequency_hz"] > f), None)
    if lower is None or upper is None:
        p = lower or upper
        decades = abs(math.log10(f / p["frequency_hz"]))
        widen = 1 + decades
        return dict(
            p,
            distance_sd_m=p["distance_sd_m"] * widen + p["distance_m"] * 0.25 * decades,
            bearing_sd_deg=_min(90, p["bearing_sd_deg"] * widen),
            method=(
                f"εκτός εύρους βαθμονόμησης (πλησιέστερη {fmt_hz(p['frequency_hz'])}, "
                f"{_js_string(round_js(decades, 2))} δεκάδες μακριά)"
            ),
            extrapolated=True,
        )
    t = math.log10(f / lower["frequency_hz"]) / math.log10(upper["frequency_hz"] / lower["frequency_hz"])

    def lerp(a, b):
        return a + (b - a) * t

    # Between two measured points the truth may not lie on the straight line:
    # add half the jump between them to the spread.
    jump = abs(upper["distance_m"] - lower["distance_m"]) / 2
    bearing_step = angle_diff(lower["relative_bearing_deg"], upper["relative_bearing_deg"])
    return {
        "frequency_hz": f,
        "n": 0,
        "distance_m": lerp(lower["distance_m"], upper["distance_m"]),
        "relative_bearing_deg": norm(lower["relative_bearing_deg"] + bearing_step * t),
        "distance_sd_m": math.hypot(lerp(lower["distance_sd_m"], upper["distance_sd_m"]), jump),
        "bearing_sd_deg": math.hypot(lerp(lower["bearing_sd_deg"], upper["bearing_sd_deg"]), abs(bearing_step) / 2),
        "spread_measured": lower["spread_measured"] and upper["spread_measured"],
        "depth_m": lerp(lower["depth_m"], upper["depth_m"]),
        "years": lerp(lower["years"], upper["years"]),
        "spacing_m": _coalesce(lower["spacing_m"], upper["spacing_m"]),
        "sessions": list(dict.fromkeys([*lower["sessions"], *upper["sessions"]])),
        "method": f"παρεμβολή (log f) ανάμεσα σε {fmt_hz(lower['frequency_hz'])} και {fmt_hz(upper['frequency_hz'])}",
        "extrapolated": False,
    }


def target_body(length_m: float, width_m: float, height_m: float, coins: float, years: float) -> dict:
    """The buried body: equivalent sphere of the box plus the corrosion halo of its age."""
    volume = length_m * width_m * height_m
    sphere = _cbrt((3 * volume) / (4 * math.pi))
    halo = _min(HALO_MAX_M, HALO_M_PER_SQRT_YEAR * math.sqrt(_max(0, years)))
    if coins:
        gold = _js_string(round_js(coins * SOVEREIGN["gold_g"], 3))
        note = (
            f"{_js_string(coins)} λίρες ≈ {gold} g χρυσού, όγκος μικρός μπροστά στο κιβώτιο· η γεωμετρία καθορίζεται "
            "από το κιβώτιο. Ο χρυσός μετρά στο κανάλι Au και στο γαλβανικό ζεύγος χρυσού–χάλυβα "
            "(ισχυρότερο αυτοδυναμικό, ΥΠΟΘΕΣΗ)."
        )
    else:
        note = "Άδειο κιβώτιο."
    return {
        "box_m": [length_m, width_m, height_m],
        "equivalent_sphere_radius_m": round_js(sphere),
        "corrosion_halo_radius_m": round_js(halo),
        "effective_radius_m": sphere + halo,
        "centre_depth_offset_m": height_m / 2,
        "gold_g": round_js(coins * SOVEREIGN["gold_g"], 4) if coins else 0,
        "coins": coins,
        "note": note,
    }


def destination(lat: float, lon: float, bearing_deg: float, distance_m: float) -> dict:
    d = distance_m / EARTH_R
    b = bearing_deg * DEG
    p1 = lat * DEG
    l1 = lon * DEG
    p2 = _asin(_sin(p1) * _cos(d) + _cos(p1) * _sin(d) * _cos(b))
    l2 = l1 + math.atan2(_sin(b) * _sin(d) * _cos(p1), _cos(d) - _sin(p1) * _sin(p2))
    return {"lat": round_js(p2 / DEG, 9), "lon": round_js(norm(l2 / DEG + 180) - 180, 9)}


def destination_xy(lat0: float, lon0: float, x: float, y: float) -> dict:
    dist = math.hypot(x, y)
    if dist < 1e-6:
        return {"lat": round_js(lat0, 9), "lon": round_js(lon0, 9)}
    return destination(lat0, lon0, norm(math.atan2(x, y) / DEG), dist)


def predict_at(cal: dict, body: dict, cal_body: dict, depth: float, years: float, spacing_mismatch: bool) -> dict:
    zc = depth + body["centre_depth_offset_m"]
    zc0 = cal["depth_m"] + cal_body["centre_depth_offset_m"]
    # Dipole-like surface anomaly of a conductive body ~ (a/z)^3 (hypothesis for the rods' trigger).
    strength = _div(
        _pow(_div(body["effective_radius_m"], zc), 3),
        _pow(_div(cal_body["effective_radius_m"], zc0), 3),
    )
    d0 = cal["distance_m"]
    scenarios = {
        "A": d0,
        "B": d0 + _max(0, zc - zc0) * math.tan(45 * DEG),
        "C": d0 * _min(2, _max(1, _pow(strength, -1 / 6))),
    }
    central = 0
    for k, v in scenarios.items():
        central = central + WEIGHTS[k] * v
    lo = _min(*scenarios.values())
    hi = _max(*scenarios.values())
    cal_sd = cal["distance_sd_m"] * (1.5 if spacing_mismatch else 1)
    # Search radius around the predicted target point: model spread, calibration
    # spread, the depth (a buried body smears its surface footprint ~ its depth)
    # and the target's own size.
    radius = _sqrt(((hi - lo) / 2) ** 2 + cal_sd**2 + (depth / 2) ** 2 + body["effective_radius_m"] ** 2)
    return {
        "zc": zc,
        "strength": strength,
        "scenarios": scenarios,
        "central": central,
        "lo": lo,
        "hi": hi,
        "calSd": cal_sd,
        "radius": radius,
    }


# ---------------------------------------------------------------------------
# Stake spacing (galvanic, ΓΝΩΣΤΗ ΦΥΣΙΚΗ): two point electrodes at spacing L
# on a homogeneous half-space. The horizontal current density under the
# midpoint at depth z is ~ L / (L^2/4 + z^2)^(3/2), maximal at L = sqrt(2)*z,
# and the share of the current that flows below z is 1 - (2/pi)*atan(2z/L).

SPACING_TABLE_M = [0.1, 0.2, 0.3, 0.45, 0.6, 0.7, 1.0]
SPACING_BAND = 0.9


def _current_at(spacing: float, z: float) -> float:
    return _div(spacing, _pow((spacing * spacing) / 4 + z * z, 1.5))


def _share_below(spacing: float, z: float) -> float:
    return 1 - (2 / math.pi) * math.atan(_div(2 * z, spacing))


def solve_spacing(rel, target: float, lo: float, hi: float) -> float:
    """Spacing L where rel(L) = target, searched on the monotonic side [lo, hi]."""
    rising = rel(hi) > rel(lo)
    for _ in range(60):
        mid = (lo + hi) / 2
        if (rel(mid) < target) == rising:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def stake_spacing(depth: float, height: float = AMMO_BOX["height_m"], current=None, frequency=None, soil=None) -> dict:
    soil = soil if soil is not None else SOILS["medium"]
    has_current = current is not None and current > 0
    zc = depth + height / 2
    best = math.sqrt(2) * zc
    peak = _current_at(best, zc)

    def rel(spacing):
        return _div(_current_at(spacing, zc), peak)

    band = [solve_spacing(rel, SPACING_BAND, 1e-3, best), solve_spacing(rel, SPACING_BAND, best, 50 * best)]

    best_rounded = round_js(best, 2)
    candidates = [*SPACING_TABLE_M, best_rounded, *([current] if has_current else [])]
    spacings = sorted(dict.fromkeys(candidates), key=lambda v: 0 if v is None else v)
    table = []
    for spacing in spacings:
        row = {
            "spacing_m": spacing,
            "current_at_target_pct": _math_round(rel(spacing) * 100),
            "current_below_target_top_pct": _math_round(_share_below(spacing, depth) * 100),
        }
        if spacing == best_rounded:
            row["note"] = "βέλτιστη"
        if current is not None and spacing == current:
            row["note"] = "βέλτιστη = τωρινή" if spacing == best_rounded else "τωρινή"
        table.append(row)

    notes = [
        "Κανόνας: L ≈ 1,4 × βάθος κέντρου στόχου. Η καμπύλη είναι επίπεδη κοντά στο μέγιστο, οπότε ό,τι είναι μέσα "
        "στη ζώνη 90% δουλεύει σχεδόν το ίδιο.",
        "Αλλαγή απόστασης καρφιών σημαίνει νέα βαθμονόμηση: η απόκλιση του τελικού σημείου μετρήθηκε με άλλη απόσταση. "
        "Δοκίμασε τωρινή / βέλτιστη / ~1,5× βέλτιστη στο κιβώτιο βαθμονόμησης, 3 επαναλήψεις η καθεμία, και κατέγραψε "
        "με record_calibration (stake_spacing_m).",
    ]
    if frequency is not None and frequency > 0:
        w = wave(frequency, soil["permittivity"], soil["conductivity"])
        if w["loss_tangent"] < 1:
            notes.append(
                f"Στα {fmt_hz(frequency)} το έδαφος δεν είναι πια κυρίως αγώγιμο (loss tangent "
                f"{_js_string(w['loss_tangent'])}, όριο ~{fmt_hz(w['corner_frequency_hz'])}): τα καρφιά δουλεύουν και "
                "ως μικρές κεραίες και ο γαλβανικός κανόνας περιγράφει μόνο το μέρος του ρεύματος που ρέει στο χώμα. "
                "Αν οι βέργες αποκρίνονται σε αυτό είναι ΥΠΟΘΕΣΗ προς δοκιμή."
            )

    result = {
        "label": "ΓΝΩΣΤΗ ΦΥΣΙΚΗ (γαλβανική έγχυση ρεύματος, ομογενές έδαφος)· ότι οι βέργες ακολουθούν το ρεύμα "
        "στον στόχο είναι ΥΠΟΘΕΣΗ.",
        "target_centre_depth_m": round_js(zc),
        "recommended_m": best_rounded,
        "good_range_m": [round_js(band[0], 2), round_js(band[1], 2)],
    }
    if has_current:
        result["current_m"] = current
        result["current_share_of_max_pct"] = _math_round(rel(current) * 100)
        result["gain_if_recommended"] = round_js(_div(1, rel(current)), 3)
    result["sensitivity_table"] = table
    result["notes"] = notes
    return result


# ---------------------------------------------------------------------------
# Single frequency


def _now_year() -> float:
    now = datetime.now(timezone.utc)
    return now.year + (now.month - 1) / 12


def compute_deviation(args: dict, all_records: list[dict]) -> dict:
    """The model for one frequency. Returns ``{"result", ...internals}`` or ``{"ok": False, "error"}``."""
    raw_channel = _prop(args, "channel")
    channel = _js_string(raw_channel if _js_truthy(raw_channel) else "mn").lower().strip()
    f = num(_prop(args, "frequency_hz"), None)
    if f is None or not (0 < f <= 2e10):
        return {"ok": False, "error": "frequency_hz_required"}
    depth = num(_prop(args, "target_depth_m"), 0.35)
    if not (0 <= depth <= 10):
        return {"ok": False, "error": "invalid_depth"}
    now_year = _now_year()
    burial_year = _prop(args, "burial_year")
    if not _nullish(burial_year):
        years = _max(0, now_year - num(burial_year, now_year))
    else:
        years = num(_prop(args, "years_buried"), 75)
    coins = _max(0.0, _math_round(num(_prop(args, "coins"), 0)))
    generator_bearing = norm(num(_prop(args, "generator_bearing_deg"), 0))
    raw_soil = _prop(args, "soil")
    soil_key = raw_soil if isinstance(raw_soil, str) and raw_soil in SOILS else "medium"
    spacing = num(_prop(args, "stake_spacing_m"), None)

    records = [r for r in all_records if r["channel"] == channel]
    channel_note = None
    if not group_by_frequency(records):
        records = all_records
        channel_note = (
            f"Δεν υπάρχει βαθμονόμηση για το κανάλι «{channel}»· χρησιμοποιούνται όλα τα κανάλια μαζί (Mn, B) με "
            f"διπλάσια αβεβαιότητα. Χρειάζεται μέτρηση {channel} στο δοκιμαστήριο."
        )
    points = group_by_frequency(records)
    if not points:
        return {"ok": False, "error": "no_calibration_records"}
    widen_channel = 2 if channel_note else 1

    box = {
        "length_m": num(_prop(args, "box_length_m"), AMMO_BOX["length_m"]),
        "width_m": num(_prop(args, "box_width_m"), AMMO_BOX["width_m"]),
        "height_m": num(_prop(args, "box_height_m"), AMMO_BOX["height_m"]),
    }
    body = target_body(box["length_m"], box["width_m"], box["height_m"], coins, years)

    def for_cal(cal):
        return target_body(AMMO_BOX["length_m"], AMMO_BOX["width_m"], AMMO_BOX["height_m"], 0, cal["years"])

    def run(cal):
        cal_spacing = cal["spacing_m"]
        mismatch = (
            spacing is not None
            and cal_spacing is not None
            and (_div(spacing, cal_spacing) > 1.5 or _div(cal_spacing, spacing) > 1.5)
        )
        cal_w = dict(
            cal,
            distance_sd_m=cal["distance_sd_m"] * widen_channel,
            bearing_sd_deg=_min(90, cal["bearing_sd_deg"] * widen_channel),
        )
        return {
            "cal": cal_w,
            "spacingMismatch": mismatch,
            **predict_at(cal_w, body, for_cal(cal), depth, years, mismatch),
        }

    at = run(interpolate(points, f))
    offset_bearing = norm(at["cal"]["relative_bearing_deg"] + generator_bearing)
    toward_target = norm(offset_bearing + 180)
    soil = SOILS[soil_key]
    w = wave(f, soil["permittivity"], soil["conductivity"])
    spacing_advice = stake_spacing(depth, height=box["height_m"], current=spacing, frequency=f, soil=soil)

    # Frequencies that look best for this target: small transferred offset,
    # small search radius, little soil loss down to the target and back.
    ranking = []
    for p in points:
        r = run(dict(p, method="μετρημένη συχνότητα"))
        loss = wave(p["frequency_hz"], soil["permittivity"], soil["conductivity"])["attenuation_db_per_m"] * 2 * r["zc"]
        ranking.append(
            {
                "frequency": fmt_hz(p["frequency_hz"]),
                "frequency_hz": p["frequency_hz"],
                "expected_offset_m": round_js(r["central"]),
                "search_radius_m": round_js(r["radius"]),
                "soil_loss_two_way_db": round_js(loss),
                "repeats": p["n"],
            }
        )
    ranking.sort(key=lambda e: (e["expected_offset_m"] or 0) + (e["search_radius_m"] or 0))

    cal_used = at["cal"]
    calibration_used = {
        "method": cal_used["method"],
        "calibrated_offset_m": round_js(cal_used["distance_m"]),
        "calibrated_bearing_relative_to_generator_deg": round_js(cal_used["relative_bearing_deg"]),
        "calibration_target": (
            f"κιβώτιο {_js_string(round_js(cal_used['depth_m']))} m, {_js_string(round_js(cal_used['years']))} έτη"
        ),
        "spread_measured": cal_used["spread_measured"],
        "distance_sd_m": round_js(cal_used["distance_sd_m"]),
        "bearing_sd_deg": round_js(cal_used["bearing_sd_deg"]),
        "sessions": cal_used["sessions"],
    }
    if channel_note:
        calibration_used["channel_note"] = channel_note

    prediction = {
        "expected_offset_m": round_js(at["central"]),
        "offset_range_m": [round_js(_max(0, at["lo"] - at["calSd"])), round_js(at["hi"] + at["calSd"])],
        "offset_bearing_from_target_deg": round_js(offset_bearing),
        "bearing_range_deg": [
            round_js(norm(offset_bearing - cal_used["bearing_sd_deg"])),
            round_js(norm(offset_bearing + cal_used["bearing_sd_deg"])),
        ],
        "search_from_final_point": {
            "walk_bearing_deg": round_js(toward_target),
            "walk_distance_m": round_js(at["central"]),
            "search_radius_m": round_js(at["radius"]),
            "instruction": (
                f"Από το τελικό σημείο των βεργών, προχώρα {_to_fixed(at['central'])} m με διόπτευση "
                f"{_js_string(_math_round(toward_target))}° και ψάξε σε κύκλο ακτίνας {_to_fixed(at['radius'])} m."
            ),
        },
    }
    final_lat = _prop(args, "final_lat")
    final_lon = _prop(args, "final_lon")
    if not _nullish(final_lat) and not _nullish(final_lon):
        prediction["estimated_target"] = destination(num(final_lat, 0), num(final_lon, 0), toward_target, at["central"])

    warnings = []
    share = spacing_advice.get("current_share_of_max_pct")
    if share is not None and share < 80:
        warnings.append(
            f"Με καρφιά στα {_js_string(spacing)} m ο στόχος δέχεται {_js_string(share)}% του μέγιστου ρεύματος· "
            f"στα {_js_string(spacing_advice['recommended_m'])} m δέχεται "
            f"×{_js_string(spacing_advice['gain_if_recommended'])} (βλ. stake_spacing)."
        )
    if cal_used["extrapolated"]:
        warnings.append("Η συχνότητα είναι εκτός του βαθμονομημένου εύρους· η πρόβλεψη είναι πολύ αβέβαιη.")
    if at["spacingMismatch"]:
        warnings.append(
            f"Απόσταση καρφιών {_js_string(spacing)} m ≠ βαθμονόμησης {_js_string(cal_used['spacing_m'])} m· "
            "η βαθμονόμηση μεταφέρεται με ×1.5 αβεβαιότητα. Βαθμονόμησε με την ίδια απόσταση."
        )
    if not cal_used["spread_measured"]:
        warnings.append(
            "Χωρίς επαναλήψεις στη συχνότητα αυτή: η διασπορά υποτέθηκε ±35%. Τρεις επαναλήψεις τη μετρούν πραγματικά."
        )
    warnings.append(
        "Η διόπτευση μεταφέρεται σχετικά με τη θέση της γεννήτριας (στο session 5 η γεννήτρια ήταν βόρεια του "
        "στόχου). Βάλε generator_bearing_deg = διόπτευση από την περιοχή αναζήτησης προς τη γεννήτρια."
    )

    result = {
        "ok": True,
        "label": "ΥΠΟΘΕΣΗ — μοντέλο μεταφοράς βαθμονόμησης, όχι μέτρηση. Ισχύει μόνο με ίδια διάταξη (καρφιά, "
        "απόσταση/θέση γεννήτριας, χρόνος φόρτισης).",
        "input": {
            "channel": channel,
            "frequency": fmt_hz(f),
            "target_depth_m": depth,
            "years_buried": round_js(years, 3),
            "coins": coins,
            "generator_bearing_deg": generator_bearing,
            "soil": soil_key,
            "stake_spacing_m": spacing,
        },
        "calibration_used": calibration_used,
        "target_model": body,
        "relative_anomaly_strength": {
            "vs_calibration": round_js(at["strength"]),
            "db": round_js(10 * _log10(at["strength"])),
            "note": "Δίπολο (a/z)³ με a = ισοδύναμη σφαίρα + άλω διάβρωσης. <1 = ασθενέστερο ίχνος από το "
            "δοκιμαστήριο.",
        },
        "scenarios_offset_m": {
            "A_geometry": round_js(at["scenarios"]["A"]),
            "B_oblique_projection": round_js(at["scenarios"]["B"]),
            "C_weaker_target": round_js(at["scenarios"]["C"]),
            "weights": dict(WEIGHTS),
        },
        "prediction": prediction,
        "frequency_physics": {
            "wavelength_in_air_m": w["wavelength_in_air_m"],
            "wavelength_in_soil_m": w["wavelength_in_soil_m"],
            "standing_wave_spacing_air_m": w["standing_wave_spacing_air_m"],
            "soil_loss_to_target_and_back_db": round_js(w["attenuation_db_per_m"] * 2 * at["zc"]),
            "regime": w["regime"],
        },
        "frequency_ranking": ranking,
        "stake_spacing": spacing_advice,
        "warnings": warnings,
        "improve": "Κάθε νέα μέτρηση σε γνωστό στόχο (record_calibration) στενεύει το μοντέλο. Μεγαλύτερο κέρδος: "
        "κιβώτιο στα 30–50 cm στο δοκιμαστήριο, 3 επαναλήψεις ανά συχνότητα, δεύτερη θέση γεννήτριας.",
    }
    return {"result": result, "at": at, "towardTarget": toward_target, "body": body, "depth": depth}


# ---------------------------------------------------------------------------
# Triangulation: final points of the rods at 2-3 frequencies from the same
# generator position. Each point plus its own predicted offset gives one
# estimate of the target with an elliptical uncertainty (along the offset:
# scenario and calibration spread; across it: bearing spread). The estimates
# are combined by inverse-covariance weighting; their mutual distances tell
# whether they really converge.

MAX_TRI_POINTS = 6
# Mahalanobis^2 above this (2 degrees of freedom, ~95%) = the point does not agree with the others.
CHI2_95 = 5.99


def covariance(along_sd: float, across_sd: float, iso_sd: float, bearing_deg: float) -> list[list[float]]:
    b = bearing_deg * DEG
    u = [_sin(b), _cos(b)]  # east, north of the offset direction
    v = [_cos(b), -_sin(b)]
    a2 = along_sd**2
    c2 = across_sd**2
    i2 = iso_sd**2
    return [
        [a2 * u[0] * u[0] + c2 * v[0] * v[0] + i2, a2 * u[0] * u[1] + c2 * v[0] * v[1]],
        [a2 * u[0] * u[1] + c2 * v[0] * v[1], a2 * u[1] * u[1] + c2 * v[1] * v[1] + i2],
    ]


def invert(m: list[list[float]]) -> list[list[float]]:
    (a, b), (c, d) = m
    det = a * d - b * c
    return [[_div(d, det), _div(-b, det)], [_div(-c, det), _div(a, det)]]


def ellipse(m: list[list[float]]) -> dict:
    """Semi-axes (1 sigma) and orientation of a 2x2 covariance."""
    (a, b), (_, d) = m
    tr = a + d
    disc = _sqrt(((a - d) / 2) ** 2 + b * b)
    l1 = tr / 2 + disc
    l2 = _max(0, tr / 2 - disc)
    # Major-axis direction as a compass bearing (east = x, north = y).
    theta = math.atan2(l1 - a, b if _js_truthy(b) else 1e-12)
    return {"major_m": _sqrt(l1), "minor_m": _sqrt(l2), "major_axis_bearing_deg": _jsmod(norm(90 - theta / DEG), 180)}


def triangulate_target(args: dict) -> dict:
    points_arg = _prop(args, "points")
    raw = points_arg[:MAX_TRI_POINTS] if isinstance(points_arg, list) else []
    if len(raw) < 2:
        return {"ok": False, "error": "need_at_least_two_points"}
    all_records = list_calibrations()

    def number_of(p, key):
        return _js_number(_prop(p, key))

    has_gps = all(math.isfinite(number_of(p, "lat")) and math.isfinite(number_of(p, "lon")) for p in raw)
    has_local = all(math.isfinite(number_of(p, "east_m")) and math.isfinite(number_of(p, "north_m")) for p in raw)
    if not has_gps and not has_local:
        return {"ok": False, "error": "points_need_lat_lon_or_east_north"}
    lat0 = number_of(raw[0], "lat") if has_gps else 0
    lon0 = number_of(raw[0], "lon") if has_gps else 0

    def to_xy(p):
        if has_gps:
            return [
                (number_of(p, "lon") - lon0) * DEG * EARTH_R * math.cos(lat0 * DEG),
                (number_of(p, "lat") - lat0) * DEG * EARTH_R,
            ]
        return [number_of(p, "east_m"), number_of(p, "north_m")]

    estimates = []
    for p in raw:
        sub_args = dict(
            args,
            frequency_hz=_prop(p, "frequency_hz"),
            channel=_coalesce(_prop(p, "channel"), _prop(args, "channel")),
        )
        out = compute_deviation(sub_args, all_records)
        if "result" not in out:
            return {"ok": False, "error": out.get("error"), "point": p}
        at = out["at"]
        toward = out["towardTarget"]
        x0, y0 = to_xy(p)
        x = x0 + at["central"] * _sin(toward * DEG)
        y = y0 + at["central"] * _cos(toward * DEG)
        along_sd = math.hypot((at["hi"] - at["lo"]) / 2, at["calSd"])
        across_sd = at["central"] * _tan(_min(60, at["cal"]["bearing_sd_deg"]) * DEG)
        iso_sd = math.hypot(out["depth"] / 2, out["body"]["effective_radius_m"])
        estimates.append(
            {
                "p": p,
                "out": out,
                "x": x,
                "y": y,
                "cov": covariance(along_sd, across_sd, iso_sd, toward),
                "isoSd": iso_sd,
            }
        )

    def fuse(items):
        w_m = [[0, 0], [0, 0]]
        wx = [0, 0]
        for e in items:
            inv = invert(e["cov"])
            w_m = [
                [w_m[0][0] + inv[0][0], w_m[0][1] + inv[0][1]],
                [w_m[1][0] + inv[1][0], w_m[1][1] + inv[1][1]],
            ]
            wx = [
                wx[0] + inv[0][0] * e["x"] + inv[0][1] * e["y"],
                wx[1] + inv[1][0] * e["x"] + inv[1][1] * e["y"],
            ]
        cov = invert(w_m)
        return {
            "C": cov,
            "x": cov[0][0] * wx[0] + cov[0][1] * wx[1],
            "y": cov[1][0] * wx[0] + cov[1][1] * wx[1],
        }

    fused = fuse(estimates)
    cov = fused["C"]
    cx = fused["x"]
    cy = fused["y"]

    def where(x, y):
        return destination_xy(lat0, lon0, x, y) if has_gps else {"east_m": round_js(x), "north_m": round_js(y)}

    per_point = []
    for e in estimates:
        dx = e["x"] - cx
        dy = e["y"] - cy
        inv = invert(e["cov"])
        m2 = dx * (inv[0][0] * dx + inv[0][1] * dy) + dy * (inv[1][0] * dx + inv[1][1] * dy)
        r = e["out"]["result"]
        walk = r["prediction"]["search_from_final_point"]
        per_point.append(
            {
                "frequency": r["input"]["frequency"],
                "channel": r["input"]["channel"],
                "walk_bearing_deg": walk["walk_bearing_deg"],
                "walk_distance_m": walk["walk_distance_m"],
                "single_search_radius_m": walk["search_radius_m"],
                "target_estimate": where(e["x"], e["y"]),
                "distance_from_combined_m": round_js(math.hypot(dx, dy)),
                "agrees": m2 <= CHI2_95,
            }
        )
    max_spread = 0
    for i in range(len(estimates)):
        for j in range(i + 1, len(estimates)):
            max_spread = _max(
                max_spread,
                math.hypot(estimates[i]["x"] - estimates[j]["x"], estimates[i]["y"] - estimates[j]["y"]),
            )

    # The estimates share the generator geometry and the same single calibration
    # session, so their errors are partly common: do not let the combined
    # radius shrink below the target's own footprint or half the best single radius.
    ell = ellipse(cov)
    independent = _sqrt(cov[0][0] + cov[1][1])
    floor = _max(*(e["isoSd"] for e in estimates), 0.5 * _min(*(e["out"]["at"]["radius"] for e in estimates)))
    radius = _max(independent, floor, max_spread / 2)
    disagree = [p for p in per_point if not p["agrees"]]
    # With an outlier, also give the position from the points that agree.
    agreeing = [e for i, e in enumerate(estimates) if per_point[i]["agrees"]]
    without_outliers = None
    if disagree and len(agreeing) >= 2:
        g = fuse(agreeing)
        r = _max(_sqrt(g["C"][0][0] + g["C"][1][1]), floor)
        without_outliers = {
            "target": where(g["x"], g["y"]),
            "search_radius_m": round_js(r),
            "frequencies": [p["frequency"] for p in per_point if p["agrees"]],
        }

    if disagree:
        convergence = (
            f"ΔΕΝ συγκλίνουν πλήρως: {', '.join(p['frequency'] for p in disagree)} πέφτει έξω από το 95%. "
            "Πιθανό αλλαγμένο setup, λάθος καταγραφή, ή η βαθμονόμηση δεν μεταφέρεται σε αυτή τη συχνότητα. "
            "Επανάλαβε αυτή τη μέτρηση."
        )
    else:
        convergence = "Οι εκτιμήσεις συγκλίνουν (όλες μέσα στο 95% της συνδυασμένης θέσης)."

    result = {
        "ok": True,
        "label": "ΥΠΟΘΕΣΗ — συνδυασμός προβλέψεων του μοντέλου απόκλισης· όχι μέτρηση.",
        "method": "Κάθε τελικό σημείο + η απόκλιση της συχνότητάς του → μία εκτίμηση στόχου με ελλειπτική "
        "αβεβαιότητα· στάθμιση αντίστροφης συνδιακύμανσης.",
        "combined_target": where(cx, cy),
        "search_radius_m": round_js(radius),
        "uncertainty_ellipse_1sigma": {
            "major_m": round_js(ell["major_m"]),
            "minor_m": round_js(ell["minor_m"]),
            "major_axis_bearing_deg": round_js(ell["major_axis_bearing_deg"]),
        },
        "radius_if_independent_m": round_js(independent),
        "spread_between_estimates_m": round_js(max_spread),
        "convergence": convergence,
    }
    if without_outliers:
        result["combined_without_outliers"] = without_outliers
    reference = "" if has_gps else " (μέτρα ανατολικά/βόρεια από το σημείο αναφοράς σου)"
    result.update(
        {
            "points": per_point,
            "stake_spacing": estimates[0]["out"]["result"]["stake_spacing"],
            "instruction": f"Ψάξε σε κύκλο ακτίνας {_to_fixed(radius)} m γύρω από τη συνδυασμένη θέση{reference}. "
            "Επιβεβαίωσε με ανιχνευτή μετάλλων.",
            "caveats": [
                "Όλα τα σημεία πρέπει να είναι από την ΙΔΙΑ θέση γεννήτριας και ίδια απόσταση καρφιών.",
                "Τα σφάλματα των συχνοτήτων είναι εν μέρει κοινά (ίδια γεωμετρία, μία session βαθμονόμησης)· γι’ αυτό "
                "η ακτίνα δεν πέφτει κάτω από το αποτύπωμα του στόχου ή το μισό της καλύτερης μεμονωμένης ακτίνας.",
                *(
                    [
                        "Το GPS κινητού έχει σφάλμα 3–5 m· για ακρίβεια μέτρησε με μετροταινία από σταθερό σημείο "
                        "(east_m/north_m) ή μέσο όρο πολλών GPS λήψεων."
                    ]
                    if has_gps
                    else []
                ),
            ],
        }
    )
    return result


# ---------------------------------------------------------------------------
# Entry point


def _field_deviation(args: dict) -> dict:
    final_points = _prop(args, "final_points")
    if isinstance(final_points, list) and len(final_points) >= 2:
        return triangulate_target(dict(args, points=final_points))
    # Spacing advice alone: no frequency, no final points.
    if _nullish(_prop(args, "frequency_hz")) and not isinstance(final_points, list):
        depth = num(_prop(args, "target_depth_m"), None)
        if depth is None or not (0 <= depth <= 10):
            return {"ok": False, "error": "frequency_hz_or_target_depth_required"}
        soil = _prop(args, "soil")
        return {
            "ok": True,
            "stake_spacing": stake_spacing(
                depth,
                height=num(_prop(args, "box_height_m"), AMMO_BOX["height_m"]),
                current=num(_prop(args, "stake_spacing_m"), None),
                soil=SOILS[soil] if isinstance(soil, str) and soil in SOILS else SOILS["medium"],
            ),
        }
    if isinstance(final_points, list) and len(final_points) == 1:
        p = final_points[0]
        args = dict(
            args,
            frequency_hz=_prop(p, "frequency_hz"),
            channel=_coalesce(_prop(p, "channel"), _prop(args, "channel")),
            final_lat=_prop(p, "lat"),
            final_lon=_prop(p, "lon"),
        )
    out = compute_deviation(args, list_calibrations())
    return out.get("result", out)


def field_deviation(args: dict) -> dict:
    """Deviation between the rods' final point and the target (single frequency, spacing advice or triangulation).

    Read-only: uses the static calibration records only. Invalid input returns ``{"ok": False, "error": ...}``.
    """
    if not isinstance(args, dict):
        return {"ok": False, "error": "invalid_arguments"}
    try:
        return _json_ready(_field_deviation(args))
    except (ArithmeticError, ValueError, TypeError):
        # JavaScript would carry NaN/Infinity through; never turn odd input into a server error.
        return {"ok": False, "error": "computation_failed"}
