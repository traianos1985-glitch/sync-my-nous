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
