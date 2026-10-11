"""Static contract audit between the App Builder UI config and Flask routes.

This is a source-level consistency check, not a live API probe or proof of runtime
compatibility. It intentionally audits the App Builder section only.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_SECTION = re.compile(
    r"(?ms)^  appbuilder:\s*\{(?P<section>.*?)^  \},\s*^  scheduler:",
)
_PATH = re.compile(r"""path:\s*["']([^"']+)["']""")
_ROUTE = re.compile(
    r"""@app\.route\(\s*["']([^"']+)["']\s*(?:,\s*methods\s*=\s*\[([^\]]*)\])?\s*\)"""
)
_METHOD = re.compile(r"""["'](GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)["']""", re.I)


def _path_only(path: str) -> str:
    return path.split("?", 1)[0].rstrip("/") or "/"


def _ui_contract(ui_source: str) -> tuple[list[dict[str, str]], list[str]]:
    match = _SECTION.search(ui_source)
    if not match:
        return [], ["appbuilder_section_not_found"]
    section = match.group("section")
    endpoint_match = re.search(r"(?s)\bendpoints:\s*\[(.*?)\]\s*,\s*actions:", section)
    action_match = re.search(r"(?s)\bactions:\s*\[(.*)\]\s*$", section)
    if not endpoint_match or not action_match:
        return [], ["appbuilder_endpoints_or_actions_not_parseable"]

    entries: list[dict[str, str]] = []
    for path in _PATH.findall(endpoint_match.group(1)):
        entries.append({"path": _path_only(path), "method": "GET", "kind": "endpoint"})
    for path in _PATH.findall(action_match.group(1)):
        entries.append({"path": _path_only(path), "method": "POST", "kind": "action"})
    if not entries:
        return [], ["appbuilder_has_no_contract_entries"]
    return entries, []


def _backend_routes(router_source: str) -> dict[str, set[str]]:
    routes: dict[str, set[str]] = {}
    for match in _ROUTE.finditer(router_source):
        path = _path_only(match.group(1))
        methods = {method.upper() for method in _METHOD.findall(match.group(2) or "")}
        if not methods:
            methods = {"GET"}
        routes.setdefault(path, set()).update(methods)
    return routes


def audit_app_builder_contract_sources(
    ui_source: str, router_source: str
) -> dict[str, Any]:
    """Compare configured App Builder UI calls with statically declared Flask routes."""
    entries, parse_errors = _ui_contract(ui_source)
    routes = _backend_routes(router_source)
    findings: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for entry in entries:
        path, method, kind = entry["path"], entry["method"], entry["kind"]
        identity = (path, method, kind)
        if identity in seen:
            findings.append({
                "severity": "warning",
                "code": "duplicate_ui_contract_entry",
                "path": path,
                "message": f"Duplicate {kind} declaration for {path}",
            })
            continue
        seen.add(identity)
        available = routes.get(path)
        if available is None:
            findings.append({
                "severity": "error",
                "code": "ui_route_missing_in_backend",
                "path": path,
                "message": f"UI {kind} points to a route not declared in router.py: {path}",
            })
        elif method not in available:
            findings.append({
                "severity": "error",
                "code": "ui_method_not_supported",
                "path": path,
                "message": f"UI expects {method}, backend declares {', '.join(sorted(available))}",
            })

    findings.extend({
        "severity": "error",
        "code": "contract_parse_error",
        "path": "",
        "message": error,
    } for error in parse_errors)
    errors = sum(item["severity"] == "error" for item in findings)
    return {
        "ok": errors == 0,
        "status": "passed" if errors == 0 else "failed",
        "scope": "appbuilder",
        "ui_entry_count": len(entries),
        "backend_route_count": len(routes),
        "findings": findings,
        "limitations": [
            "Static source parsing only; does not send HTTP requests or test deployed routes.",
            "Does not validate request schemas, response shapes, authentication behavior, or UI rendering.",
            "Routes registered dynamically or outside router.py may not be discovered.",
        ],
    }


def audit_repository_app_builder_contract(repo_root: str | Path) -> dict[str, Any]:
    """Audit the checked-out repository using its UI config and Flask router source."""
    root = Path(repo_root).resolve()
    ui_path = root / "src" / "components" / "nous" / "section-configs.ts"
    router_path = root / "nous-ai-os" / "executor" / "router.py"
    try:
        ui_source = ui_path.read_text(encoding="utf-8")
        router_source = router_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return {
            "ok": False,
            "status": "unavailable",
            "error": "contract_source_unavailable",
            "detail": str(exc)[:300],
            "findings": [],
        }
    return audit_app_builder_contract_sources(ui_source, router_source)
