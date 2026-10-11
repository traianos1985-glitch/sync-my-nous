import hashlib

import pytest

from executor import utility_tools
from executor.tool_catalog import get_tool, tool_catalog


@pytest.mark.parametrize(("expression", "expected"), [
    ("2 + 3 * 4", 14),
    ("sqrt(81)", 9),
    ("round(pi, 3)", 3.142),
    ("-4 ** 2", -16),
])
def test_calculator_supports_safe_math(expression, expected):
    result = utility_tools.calculate(expression)
    assert result["ok"] is True
    assert result["result"] == pytest.approx(expected)


@pytest.mark.parametrize("expression", [
    "__import__('os').system('echo unsafe')",
    "open('/tmp/x')",
    "[x for x in (1, 2)]",
    "2 ** 1000",
    "float('inf')",
])
def test_calculator_rejects_unsafe_or_unbounded_expression(expression):
    result = utility_tools.calculate(expression)
    assert result["ok"] is False


def test_unit_conversion_supports_common_units():
    result = utility_tools.parse_conversion("12 km to miles")
    assert result["ok"] is True
    assert result["result"] == pytest.approx(7.456454306)
    temp = utility_tools.convert_units(32, "f", "c")
    assert temp["ok"] is True
    assert temp["result"] == pytest.approx(0)
    assert utility_tools.convert_units(1, "kg", "seconds")["ok"] is False


def test_current_time_supports_local_utc_and_iana_zone():
    local = utility_tools.current_time()
    athens = utility_tools.current_time("Europe/Athens")
    assert local["ok"] is True and local["utc"].endswith("+00:00")
    assert athens["ok"] is True and athens["timezone"] == "Europe/Athens"
    assert utility_tools.current_time("Definitely/NotAZone")["ok"] is False


def test_text_stats_and_json_validation():
    stats = utility_tools.text_stats("Hello world\n\nNOUS")
    assert stats["words"] == 3
    assert stats["lines"] == 3
    assert stats["paragraphs"] == 2
    assert utility_tools.validate_json_text('{"ok":true}')["valid"] is True
    invalid = utility_tools.validate_json_text('{"ok":}')
    assert invalid["valid"] is False
    assert invalid["line"] == 1


def test_sha256_is_stable_and_tool_catalog_is_machine_readable():
    result = utility_tools.sha256_text("NOUS")
    assert result["sha256"] == hashlib.sha256(b"NOUS").hexdigest()
    catalog = tool_catalog()
    assert catalog["ok"] is True
    assert get_tool("calculate")["approval_required"] is False
    assert get_tool("agent_solve")["approval_required"] == "depends_on_action"
    assert get_tool("does_not_exist") is None


def test_json_format_is_pretty_and_rejects_invalid_or_oversized_input():
    formatted = utility_tools.format_json('{"name":"ΝΟΥΣ","ok":true}')
    assert formatted["ok"] is True
    assert '"name": "ΝΟΥΣ"' in formatted["formatted"]
    assert formatted["type"] == "dict"
    assert utility_tools.format_json('{"broken":}')["error"] == "invalid_json"
    assert utility_tools.format_json(" " * 10_001)["error"] == "json_empty_or_too_long"


def test_url_component_encoding_round_trips_unicode_and_spaces():
    encoded = utility_tools.encode_url_component("γειά σου / NOUS")
    assert encoded["ok"] is True
    assert "%20" in encoded["encoded"] and "%2F" in encoded["encoded"]
    decoded = utility_tools.decode_url_component(encoded["encoded"])
    assert decoded == {"ok": True, "decoded": "γειά σου / NOUS"}
    assert utility_tools.decode_url_component("%FF")["error"] == "invalid_url_encoding"
    assert utility_tools.encode_url_component("x" * 10_001)["error"] == "text_too_long"

@pytest.mark.parametrize(
    ("value", "source", "target", "expected"),
    [
        (1, "mi", "m", 1609.344),
        (1, "gal", "l", 3.785411784),
        (36, "km/h", "m/s", 10),
        (212, "f", "c", 100),
        (-40, "c", "f", -40),
    ],
)
def test_unit_conversion_matches_reference_values(value, source, target, expected):
    result = utility_tools.convert_units(value, source, target)
    assert result["ok"] is True
    assert result["result"] == pytest.approx(expected)


@pytest.mark.parametrize(
    ("value", "source", "target"),
    [
        (-273.16, "c", "k"),
        (-459.68, "f", "k"),
        (-0.1, "k", "c"),
    ],
)
def test_temperature_conversion_rejects_below_absolute_zero(value, source, target):
    result = utility_tools.convert_units(value, source, target)
    assert result["ok"] is False
    assert result["error"] == "temperature_below_absolute_zero"
