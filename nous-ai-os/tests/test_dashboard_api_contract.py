import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _flask_routes():
    source = (ROOT / "nous-ai-os" / "executor" / "router.py").read_text(encoding="utf-8")
    pattern = re.compile(r"""@app\.route\(\s*["']([^"']+)["']""")
    return {match.group(1) for match in pattern.finditer(source)}


def _frontend_api_routes():
    routes = set()
    for route_file in (ROOT / "src" / "routes").glob("api.*.ts"):
        stem = route_file.name[:-3]
        if "$" in stem:
            continue
        routes.add("/" + stem.replace(".", "/"))
    return routes


def test_every_section_panel_path_has_a_real_backend_or_frontend_route():
    config = (
        ROOT / "src" / "components" / "nous" / "section-configs.ts"
    ).read_text(encoding="utf-8")
    configured_paths = {
        match.group(1).split("?", maxsplit=1)[0]
        for match in re.finditer(r'path:\s*"([^"]+)"', config)
    }
    available_routes = _flask_routes() | _frontend_api_routes()
    missing = sorted(path for path in configured_paths if path not in available_routes)
    assert not missing, "SectionPanel paths without a registered route: " + ", ".join(missing)


def test_dashboard_api_paths_are_sent_to_the_flask_base_url():
    source = (ROOT / "src" / "lib" / "nous-api.ts").read_text(encoding="utf-8")
    dashboard = (ROOT / "src" / "routes" / "dashboard.tsx").read_text(encoding="utf-8")
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
    methods = {}
    router = (
        ROOT / "nous-ai-os" / "executor" / "router.py"
    ).read_text(encoding="utf-8")
    route_pattern = re.compile(
        r"""@app\.route\(\s*["']([^"']+)["'](?:,\s*methods=\[([^\]]+)\])?\)"""
    )
    for match in route_pattern.finditer(router):
        route = match.group(1)
        declared = match.group(2)
        supported = (
            set(re.findall(r"""["'](GET|POST|PUT|PATCH|DELETE)["']""", declared))
            if declared
            else {"GET", "HEAD", "OPTIONS"}
        )
        methods.setdefault(route, set()).update(supported)

    for route_file in (ROOT / "src" / "routes").glob("api.*.ts"):
        stem = route_file.name[:-3]
        if "$" in stem:
            continue
        route = "/" + stem.replace(".", "/")
        source = route_file.read_text(encoding="utf-8")
        methods[route] = set(re.findall(r"^\s*(GET|POST|PUT|PATCH|DELETE):", source, re.MULTILINE))
    return methods


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
