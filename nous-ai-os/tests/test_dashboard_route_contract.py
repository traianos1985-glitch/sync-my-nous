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


def test_every_configured_section_is_reachable_from_navigation():
    root = Path(__file__).resolve().parents[2]
    config_source = SECTION_CONFIG.read_text(encoding="utf-8")
    nav_source = (root / "src" / "components" / "nous" / "nav.ts").read_text(encoding="utf-8")

    config_body = config_source.split("export const sectionConfigs", maxsplit=1)[1]
    configured_sections = {
        quoted or bare
        for quoted, bare in re.findall(
            r'^\\s{2}(?:"([^"]+)"|([A-Za-z_$][\\w$]*))\\s*:\\s*\\{',
            config_body,
            flags=re.MULTILINE,
        )
    }
    nav_sections = set(re.findall(r'\\bid\\s*:\\s*["\\']([^"\\']+)["\\']', nav_source))
    unreachable = sorted(configured_sections - nav_sections)

    assert not unreachable, (
        "Configured dashboard sections are not reachable from navigation: "
        + ", ".join(unreachable)
    )
