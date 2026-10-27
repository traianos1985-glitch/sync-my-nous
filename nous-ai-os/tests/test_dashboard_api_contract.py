import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _flask_route_methods():
    """Return only routes available on the deployed Flask backend.

    TanStack server handlers are not deployed by GitHub Pages and cannot satisfy
    this production contract.
    """
    methods = {}
    router = (ROOT / "nous-ai-os" / "executor" / "router.py").read_text(encoding="utf-8")
    route_pattern = re.compile(
        r"""@app\.route\(\s*["']([^"']+)["'](?:,\s*methods=\[([^\]]+)\])?\)"""
    )
    for match in route_pattern.finditer(router):
        route, declared = match.groups()
        supported = (
            set(re.findall(r"""["'](GET|POST|PUT|PATCH|DELETE)["']""", declared))
            if declared
            else {"GET", "HEAD", "OPTIONS"}
        )
        methods.setdefault(route, set()).update(supported)

    dashboard_api = (ROOT / "nous-ai-os" / "executor" / "dashboard_api.py").read_text(encoding="utf-8")
    blueprint_pattern = re.compile(
        r"""@dashboard_api_bp\.(get|post|put|patch|delete)\(["']([^"']+)["']\)"""
    )
    for match in blueprint_pattern.finditer(dashboard_api):
        method, route = match.groups()
        methods.setdefault("/api" + route, set()).add(method.upper())

    # Include the provider/environment blueprint used by the deployment panel.
    environments_bp = (
        ROOT / "nous-ai-os" / "executor" / "blueprints" / "agent_environments_bp.py"
    ).read_text(encoding="utf-8")
    environments_pattern = re.compile(
        r"""@agent_environments_bp\.(get|post|put|patch|delete)\(["']([^"']+)["']\)"""
    )
    for match in environments_pattern.finditer(environments_bp):
        method, route = match.groups()
        methods.setdefault("/api/agent-environments" + route, set()).add(method.upper())
    return methods


def _flask_routes():
    return set(_flask_route_methods())


def test_every_section_panel_path_has_a_real_flask_backend_route():
    config = (
        ROOT / "src" / "components" / "nous" / "section-configs.ts"
    ).read_text(encoding="utf-8")
    configured_paths = {
        match.group(1).split("?", maxsplit=1)[0]
        for match in re.finditer(r'path:\s*"([^"]+)"', config)
    }
    available_routes = _flask_routes()
    missing = sorted(path for path in configured_paths if path not in available_routes)
    assert not missing, "SectionPanel paths without a registered route: " + ", ".join(missing)


def test_dashboard_literal_api_calls_have_flask_routes():
    dashboard = (ROOT / "src" / "components" / "nous" / "dashboard-page.tsx").read_text(encoding="utf-8")
    methods = _flask_route_methods()
    api_aliases = {"/api/chat": "/chat", "/api/health": "/health"}
    paths = {
        match.group(1).split("?", maxsplit=1)[0]
        for match in re.finditer(r"""nousFetch(?:<[^>]*>)?\(\s*["']([^"']+)["']""", dashboard)
    }
    missing = sorted(path for path in paths if api_aliases.get(path, path) not in methods)
    assert not missing, "Dashboard API calls without a Flask route: " + ", ".join(missing)


def test_dashboard_api_paths_are_sent_to_the_flask_base_url():
    source = (ROOT / "src" / "lib" / "nous-api.ts").read_text(encoding="utf-8")
    dashboard = (ROOT / "src" / "components" / "nous" / "dashboard-page.tsx").read_text(encoding="utf-8")
    assert "FRONTEND_API_PREFIXES" not in source
    assert "isFrontendApiPath" not in source
    assert "requestUrl(path: string)" in source
    assert "resolvePath(path)" in source
    assert '"/api/chat": "/chat"' in source
    assert '"/api/health": "/health"' in source
    assert source.count("fetch(requestUrl(path), request)") == 4
    assert 'nousStream("/api/missions/stream")' not in dashboard
    assert '("/remote/missions")' in dashboard

def _action_arrays(source):
    arrays = []
    for match in re.finditer(r"actions:\s*\[", source):
        start = match.end() - 1
        depth = 0
        quote = None
        escaped = False
        for index in range(start, len(source)):
            char = source[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                continue
            if char in {"'", '"', chr(96)}:
                quote = char
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    arrays.append(source[start + 1 : index])
                    break
    return arrays


def _registered_methods():
    return _flask_route_methods()


def test_every_section_panel_action_has_a_post_handler():
    config = (
        ROOT / "src" / "components" / "nous" / "section-configs.ts"
    ).read_text(encoding="utf-8")
    action_paths = {
        match.group(1).split("?", maxsplit=1)[0]
        for body in _action_arrays(config)
        for match in re.finditer(r'path:\s*"([^"]+)"', body)
    }
    methods = _registered_methods()
    missing = sorted(path for path in action_paths if "POST" not in methods.get(path, set()))
    assert not missing, "SectionPanel actions without a POST handler: " + ", ".join(missing)
