"""Read-only project compatibility checks for external preview providers.

Only small, known manifest files are inspected. The module never executes project
commands, reads .env files, or returns manifest values that could contain secrets.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from executor.provider_runtime import _resolve_workspace_path, workspace_root

_MAX_MANIFEST_BYTES = 256 * 1024
_JS_LOCKFILES = ("pnpm-lock.yaml", "yarn.lock", "package-lock.json", "bun.lockb", "bun.lock")
_PYTHON_FRAMEWORKS = {
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
}
_JS_FRAMEWORKS = {
    "next": "Next.js",
    "vite": "Vite",
    "astro": "Astro",
    "react": "React",
    "vue": "Vue",
    "svelte": "Svelte",
    "@angular/core": "Angular",
    "nuxt": "Nuxt",
    "express": "Express",
}


def _safe_manifest(project: Path, name: str) -> Path | None:
    candidate = project / name
    if not candidate.is_file():
        return None
    try:
        candidate.resolve().relative_to(workspace_root())
    except (OSError, ValueError):
        return None
    try:
        if candidate.stat().st_size > _MAX_MANIFEST_BYTES:
            return None
    except OSError:
        return None
    return candidate


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def inspect_preview_compatibility(project_path: str = ".") -> dict[str, Any]:
    """Inspect a project without executing it and score known preview destinations."""
    try:
        project = _resolve_workspace_path(project_path)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    root = workspace_root()
    package_path = _safe_manifest(project, "package.json")
    package = _read_json(package_path)
    dependencies: set[str] = set()
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        values = package.get(section, {})
        if isinstance(values, dict):
            dependencies.update(str(name).lower() for name in values.keys())

    python_files = [
        name for name in ("pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock")
        if _safe_manifest(project, name) is not None
    ]
    lockfiles = [name for name in _JS_LOCKFILES if _safe_manifest(project, name) is not None]
    has_dockerfile = _safe_manifest(project, "Dockerfile") is not None
    has_index = _safe_manifest(project, "index.html") is not None
    scripts = package.get("scripts", {})
    script_names = sorted(str(name) for name in scripts) if isinstance(scripts, dict) else []
    framework_names = sorted({label for key, label in _JS_FRAMEWORKS.items() if key in dependencies})
    python_framework_names = sorted({label for key, label in _PYTHON_FRAMEWORKS.items()
                                     if any(re.search(rf"(?i)(^|[^a-z]){re.escape(key)}([^a-z]|$)", name)
                                            for name in python_files)})

    project_types: list[str] = []
    if package_path:
        project_types.append("node")
    if python_files:
        project_types.append("python")
    if has_dockerfile:
        project_types.append("container")
    if has_index and not package_path:
        project_types.append("static")
    if not project_types:
        project_types.append("unknown")

    if not framework_names and package_path:
        framework_names = ["Node.js project"]
    if not python_framework_names and python_files:
        python_framework_names = ["Python project"]

    javascript_ready = "node" in project_types and bool(script_names)
    fullstack = bool(dependencies & {"next", "nuxt", "astro", "vite", "express"})
    provider_rows = [
        {
            "id": "stackblitz",
            "label": "StackBlitz",
            "fit": "good" if javascript_ready else "limited",
            "recommended": javascript_ready,
            "reasons": (["Node manifest and scripts found"] if javascript_ready else
                        ["Best fit is a browser-compatible JavaScript project with runnable scripts"]),
        },
        {
            "id": "codesandbox",
            "label": "CodeSandbox",
            "fit": "good" if javascript_ready else "limited",
            "recommended": javascript_ready,
            "reasons": (["Node manifest and scripts found"] if javascript_ready else
                        ["Compatibility depends on the template and runtime supported by the imported repository"]),
        },
        {
            "id": "v0",
            "label": "v0",
            "fit": "good" if fullstack or bool(dependencies & {"react", "next"}) else "limited",
            "recommended": bool(dependencies & {"react", "next", "vite", "nuxt"}),
            "reasons": (["React/Next-style web dependencies detected"] if dependencies & {"react", "next", "vite", "nuxt"}
                        else ["Usually a stronger fit for React-oriented web apps"]),
        },
        {
            "id": "bolt",
            "label": "Bolt.new",
            "fit": "good" if javascript_ready else "limited",
            "recommended": javascript_ready,
            "reasons": (["Node manifest and scripts found"] if javascript_ready else
                        ["Best fit is a compatible JavaScript web application"]),
        },
        {
            "id": "railway",
            "label": "Railway Sandboxes",
            "fit": "good" if has_dockerfile or "python" in project_types or "node" in project_types else "unknown",
            "recommended": has_dockerfile or "python" in project_types or "node" in project_types,
            "reasons": (["Container or server runtime markers found"] if has_dockerfile or "python" in project_types or "node" in project_types
                        else ["Runtime could not be identified from the inspected manifests"]),
        },
    ]

    return {
        "ok": True,
        "project_path": str(project.relative_to(root)) or ".",
        "project_types": project_types,
        "detected": {
            "package_json": bool(package_path),
            "javascript_lockfiles": lockfiles,
            "python_manifests": python_files,
            "dockerfile": has_dockerfile,
            "static_index": has_index,
            "script_names": script_names,
            "javascript_frameworks": framework_names,
            "python_frameworks": python_framework_names,
        },
        "providers": provider_rows,
        "limitations": [
            "Read-only static inspection; no install, build, network request, or provider sandbox is started.",
            "A compatibility score is a heuristic, not a guarantee that an imported project will build.",
            "Manifest contents, environment values, source files, and secrets are not returned.",
        ],
    }
