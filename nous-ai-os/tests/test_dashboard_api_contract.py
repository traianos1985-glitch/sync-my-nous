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
        for match in re.finditer(r'path:\\s*"([^"]+)"', config)
    }
    available_routes = _flask_routes() | _frontend_api_routes()
    missing = sorted(path for path in configured_paths if path not in available_routes)
    assert not missing, "SectionPanel paths without a registered route: " + ", ".join(missing)


def test_frontend_owned_api_paths_are_not_sent_to_the_flask_base_url():
    source = (ROOT / "src" / "lib" / "nous-api.ts").read_text(encoding="utf-8")
    for path in (
        "/api/approvals",
        "/api/audit",
        "/api/evaluation",
        "/api/feedback",
        "/api/jobs",
        "/api/knowledge",
        "/api/missions",
        "/api/observability",
        "/api/security-audit",
        "/api/security-lessons",
        "/api/status",
        "/api/tools/execute",
        "/api/chat/stream",
    ):
        assert f'"{path}"' in source
    assert "function requestUrl(path: string)" in source
    assert source.count("fetch(requestUrl(path), request)") == 4
