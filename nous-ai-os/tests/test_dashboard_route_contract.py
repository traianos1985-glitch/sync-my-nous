import re
from pathlib import Path
from urllib.parse import urlsplit

from executor.router import app


REPO_ROOT = Path(__file__).resolve().parents[2]
SECTION_CONFIG = REPO_ROOT / "src" / "components" / "nous" / "section-configs.ts"
BACKEND_PATH_MAP = {
    "/api/chat": "/chat",
    "/api/health": "/health",
}


def _configured_paths():
    source = SECTION_CONFIG.read_text(encoding="utf-8")
    return sorted(
        {
            path
            for path in re.findall(r'\bpath\s*:\s*["\']([^"\']+)["\']', source)
            if path.startswith("/")
        }
    )


def _route_pattern(rule):
    # Flask variables are matched as one path segment unless declared as path converters.
    pattern = re.sub(r"<path:[^>]+>", r".+", rule)
    pattern = re.sub(r"<[^>]+>", r"[^/]+", pattern)
    return re.compile("^" + pattern.rstrip("/") + "/?$")


def _registered_paths():
    return [
        _route_pattern(rule.rule)
        for rule in app.url_map.iter_rules()
    ]


def test_dashboard_section_paths_resolve_to_registered_backend_routes():
    registered = _registered_paths()
    missing = []

    for configured in _configured_paths():
        path = urlsplit(configured).path
        path = BACKEND_PATH_MAP.get(path, path)
        if not any(pattern.match(path) for pattern in registered):
            missing.append(configured)

    assert not missing, (
        "Dashboard section-configs.ts contains paths with no registered Flask route: "
        + ", ".join(missing)
    )


def _configured_entries():
    source = SECTION_CONFIG.read_text(encoding="utf-8")
    entries = []
    for block_name, method in (("endpoints", "GET"), ("actions", "POST")):
        blocks = re.findall(rf"\b{block_name}\s*:\s*\[([\s\S]*?)\]", source)
        for block in blocks:
            for path in re.findall(r"path\s*:\s*['\"]([^'\"]+)['\"]", block):
                if path.startswith("/"):
                    entries.append((path, method, block_name))
    return entries


def test_dashboard_section_entries_use_supported_http_methods():
    entries = _configured_entries()
    assert entries, "No section-panel API entries were parsed"
    missing = []
    for configured, expected_method, kind in entries:
        path = urlsplit(configured).path
        path = BACKEND_PATH_MAP.get(path, path)
        methods = set()
        for rule in app.url_map.iter_rules():
            if _route_pattern(rule.rule).match(path):
                methods.update(rule.methods or set())
        if expected_method not in methods:
            missing.append({"configured": configured, "kind": kind, "expected": expected_method, "available": sorted(methods)})
    assert not missing, f"Dashboard section HTTP method mismatches: {missing}"


def test_every_section_config_is_reachable_from_navigation_or_custom_dashboard():
    nav_source = (REPO_ROOT / "src" / "components" / "nous" / "nav.ts").read_text(encoding="utf-8")
    nav_ids = set(re.findall(r"\bid\s*:\s*['\"]([^'\"]+)['\"]", nav_source))
    config_source = SECTION_CONFIG.read_text(encoding="utf-8")
    pairs = re.findall(r'^  (?:"([^"]+)"|([A-Za-z_$][\w$-]*)):\s*\{', config_source, re.M)
    config_ids = {first or second for first, second in pairs}
    custom_dashboard_sections = {"chat", "home", "documents", "control", "settings"}
    orphaned = sorted(config_ids - nav_ids - custom_dashboard_sections)
    assert not orphaned, f"Section configs are unreachable from navigation: {orphaned}"
def test_every_navigation_section_is_configured_or_has_an_explicit_custom_renderer():
    nav_source = (
        REPO_ROOT / "src" / "components" / "nous" / "nav.ts"
    ).read_text(encoding="utf-8")
    nav_ids = set(re.findall(r'\\bid\\s*:\\s*["\\']([^"\\']+)["\\']', nav_source))
    config_source = SECTION_CONFIG.read_text(encoding="utf-8")
    pairs = re.findall(
        r'^  (?:["]([^"]+)["]|([A-Za-z_$][\\w$-]*)):\\s*\\{',
        config_source,
        re.M,
    )
    config_ids = {first or second for first, second in pairs}
    # These sections are rendered directly in dashboard.tsx instead of SectionPanel.
    custom_sections = {"chat", "documents", "settings"}
    missing = sorted(nav_ids - config_ids - custom_sections)
    assert not missing, f"Navigation sections without a panel or custom renderer: {missing}"
