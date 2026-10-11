"""Verify section-panel calls match both Flask routes and HTTP methods."""
import re
from pathlib import Path
from urllib.parse import urlsplit

from executor.router import app


REPO_ROOT = Path(__file__).resolve().parents[2]
SECTION_CONFIG = REPO_ROOT / "src" / "components" / "nous" / "section-configs.ts"


def _configured_calls():
    source = SECTION_CONFIG.read_text(encoding="utf-8")
    calls = []
    path_pattern = re.compile(r"""\bpath\s*:\s*["']([^"']+)["']""")
    for match in path_pattern.finditer(source):
        before = source[:match.start()]
        endpoint_pos = before.rfind("endpoints:")
        action_pos = before.rfind("actions:")
        method = "POST" if action_pos > endpoint_pos else "GET"
        calls.append((urlsplit(match.group(1)).path.rstrip("/") or "/", method))
    return sorted(set(calls))


def _route_pattern(rule):
    pattern = re.sub(r"<path:[^>]+>", r".+", rule)
    pattern = re.sub(r"<[^>]+>", r"[^/]+", pattern)
    return re.compile("^" + pattern.rstrip("/") + "/?$")


def _registered_routes():
    return [
        (_route_pattern(rule.rule), set(rule.methods or ()))
        for rule in app.url_map.iter_rules()
    ]


def test_every_section_panel_call_uses_a_registered_route_and_supported_method():
    routes = _registered_routes()
    missing = []
    method_mismatches = []

    for path, expected_method in _configured_calls():
        matches = [methods for pattern, methods in routes if pattern.match(path)]
        if not matches:
            missing.append(f"{expected_method} {path}")
            continue
        if not any(expected_method in methods for methods in matches):
            supported = sorted(set().union(*matches))
            method_mismatches.append(
                f"{expected_method} {path} (backend supports: {', '.join(supported)})"
            )

    assert not missing, (
        "Section-panel calls without a registered Flask route: " + ", ".join(missing)
    )
    assert not method_mismatches, (
        "Section-panel HTTP method mismatches: " + ", ".join(method_mismatches)
    )


def test_section_panel_contract_covers_both_read_and_action_calls():
    calls = _configured_calls()
    methods = {method for _, method in calls}
    assert "GET" in methods
    assert "POST" in methods
    assert len(calls) >= 40
