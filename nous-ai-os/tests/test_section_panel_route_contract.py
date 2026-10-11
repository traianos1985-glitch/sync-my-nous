import re
from pathlib import Path


def _backend_routes(root: Path) -> set[str]:
    files = [
        root / "nous-ai-os" / "executor" / "router.py",
        root / "nous-ai-os" / "executor" / "dashboard_api.py",
        *sorted((root / "nous-ai-os" / "executor" / "blueprints").glob("*.py")),
    ]
    routes: set[str] = set()
    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        prefixes = {
            name: prefix.rstrip("/")
            for name, prefix in re.findall(
                r"(?s)(\w+)\s*=\s*Blueprint\([^)]*?url_prefix\s*=\s*[\"']([^\"']*)[\"']",
                source,
            )
        }
        decorators = re.findall(
            r"(?m)^\s*@([A-Za-z_]\w*)\.(?:route|get|post|put|patch|delete)\(\s*[\"']([^\"']+)[\"']",
            source,
        )
        for owner, path in decorators:
            prefix = prefixes.get(owner, "")
            combined = (prefix + "/" + path.lstrip("/")) if prefix else path
            routes.add(re.sub(r"/+", "/", combined))

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


def test_every_section_panel_endpoint_and_action_has_a_backend_route():
    root = Path(__file__).resolve().parents[2]
    config_path = root / "src" / "components" / "nous" / "section-configs.ts"
    config_source = config_path.read_text(encoding="utf-8")
    ui_paths = {
        match.split("?", maxsplit=1)[0]
        for match in re.findall(r"path:\s*[\"']([^\"']+)[\"']", config_source)
    }
    backend_paths = _backend_routes(root)

    missing = sorted(
        ui_path
        for ui_path in ui_paths
        if not any(_route_matches(ui_path, backend_path) for backend_path in backend_paths)
    )
    assert not missing, f"Section-panel paths without backend routes: {missing}"
