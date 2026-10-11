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
