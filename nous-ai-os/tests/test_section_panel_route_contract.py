import re
from pathlib import Path

_ROUTE_DECORATOR = re.compile(
    r"""(?m)^\s*@([A-Za-z_]\w*)\.(route|get|post|put|patch|delete)\(\s*["']([^"']+)["']([^)]*)\)"""
)
_METHODS_ARG = re.compile(r"""methods\s*=\s*\[([^\]]*)\]""")
_METHOD_NAME = re.compile(r"""["'](GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["']""", re.I)


def _backend_routes(root: Path) -> dict[str, set[str]]:
    files = [
        root / "nous-ai-os" / "executor" / "router.py",
        root / "nous-ai-os" / "executor" / "dashboard_api.py",
        *sorted((root / "nous-ai-os" / "executor" / "blueprints").glob("*.py")),
    ]
    routes: dict[str, set[str]] = {}
    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        prefixes = {
            name: prefix.rstrip("/")
            for name, prefix in re.findall(
                r"""(?s)(\w+)\s*=\s*Blueprint\([^)]*?url_prefix\s*=\s*["']([^"']*)["']""",
                source,
            )
        }
        for match in _ROUTE_DECORATOR.finditer(source):
            owner, decorator, path, arguments = match.groups()
            prefix = prefixes.get(owner, "")
            combined = (prefix + "/" + path.lstrip("/")) if prefix else path
            normalized = re.sub(r"/+", "/", combined).rstrip("/") or "/"
            if decorator == "route":
                methods_match = _METHODS_ARG.search(arguments)
                methods = (
                    {method.upper() for method in _METHOD_NAME.findall(methods_match.group(1))}
                    if methods_match
                    else {"GET", "HEAD", "OPTIONS"}
                )
            else:
                methods = {decorator.upper(), "OPTIONS"}
                if decorator.lower() == "get":
                    methods.add("HEAD")
            routes.setdefault(normalized, set()).update(methods)
    return routes


def _route_matches(ui_path: str, backend_path: str) -> bool:
    ui_parts = ui_path.split("/")
    backend_parts = backend_path.split("/")
    if len(ui_parts) != len(backend_parts):
        return False
    return all(
        actual == expected or (expected.startswith("<") and expected.endswith(">"))
        for actual, expected in zip(ui_parts, backend_parts)
    )


def _ui_contract(root: Path) -> tuple[set[str], set[str]]:
    config_path = root / "src" / "components" / "nous" / "section-configs.ts"
    config_source = config_path.read_text(encoding="utf-8")
    # SectionPanel loads endpoints with GET and dispatches actions with POST.
    endpoint_blocks = re.findall(r"(?s)\bendpoints:\s*\[(.*?)\]", config_source)
    action_blocks = re.findall(r"(?s)\bactions:\s*\[(.*?)\]", config_source)
    endpoints = {
        path.split("?", maxsplit=1)[0].rstrip("/") or "/"
        for block in endpoint_blocks
        for path in re.findall(r"""path:\s*["']([^"']+)["']""", block)
    }
    actions = {
        path.split("?", maxsplit=1)[0].rstrip("/") or "/"
        for block in action_blocks
        for path in re.findall(r"""path:\s*["']([^"']+)["']""", block)
    }
    return endpoints, actions


def test_every_section_panel_endpoint_and_action_has_a_backend_route():
    root = Path(__file__).resolve().parents[2]
    endpoints, actions = _ui_contract(root)
    backend_routes = _backend_routes(root)

    missing = sorted(
        ui_path
        for ui_path in endpoints | actions
        if not any(_route_matches(ui_path, backend_path) for backend_path in backend_routes)
    )
    assert not missing, f"Section-panel paths without backend routes: {missing}"


def test_section_panel_endpoints_and_actions_use_supported_http_methods():
    root = Path(__file__).resolve().parents[2]
    endpoints, actions = _ui_contract(root)
    backend_routes = _backend_routes(root)

    mismatches = []
    for expected_method, paths in (("GET", endpoints), ("POST", actions)):
        for ui_path in sorted(paths):
            matching = [
                methods
                for backend_path, methods in backend_routes.items()
                if _route_matches(ui_path, backend_path)
            ]
            if matching and not any(expected_method in methods for methods in matching):
                supported = sorted(set().union(*matching))
                mismatches.append(
                    f"{expected_method} {ui_path} (backend methods: {', '.join(supported)})"
                )
    assert not mismatches, "Section-panel HTTP method mismatches: " + "; ".join(mismatches)

def test_home_runtime_overview_is_rendered_by_the_home_dashboard():
    root = Path(__file__).resolve().parents[2]
    dashboard_source = (root / "src" / "routes" / "dashboard.tsx").read_text(encoding="utf-8")
    home_start = dashboard_source.index(') : section === "home" ? (')
    home_panel = dashboard_source.index('<SectionPanel section="home" />', home_start)
    home_end = dashboard_source.index('        ) : (', home_panel)
    assert home_panel < home_end, (
        "Home section config exists but is not rendered in the Home dashboard"
    )

def test_every_navigation_section_has_a_config_or_explicit_custom_renderer():
    root = Path(__file__).resolve().parents[2]
    nav_source = (root / "src" / "components" / "nous" / "nav.ts").read_text(encoding="utf-8")
    nav_ids = set(re.findall(r'id: "([^"]+)"', nav_source))
    config_source = (root / "src" / "components" / "nous" / "section-configs.ts").read_text(encoding="utf-8")
    config_ids = {
        line.strip().removesuffix(": {").strip('"')
        for line in config_source.splitlines()
        if line.startswith("  ") and line.rstrip().endswith(": {")
    }
    custom_sections = {"chat", "home", "documents", "control", "settings"}
    missing = sorted(nav_ids - config_ids - custom_sections)
    assert not missing, f"Navigation sections without a panel or custom renderer: {missing}"
