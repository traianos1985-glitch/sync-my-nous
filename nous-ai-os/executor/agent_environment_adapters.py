"""Provider-aware capability discovery for NOUS agent runtimes.

Detection is deliberately read-only: it inspects environment-variable *names* and
project marker filenames, never values, credentials, or provider account data.
It does not install packages, deploy apps, or claim ownership of external resources.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Sequence, Any


_PROVIDERS: tuple[dict[str, Any], ...] = (
    {
        "id": "vercel",
        "label": "Vercel",
        "markers": ("VERCEL", "VERCEL_ENV", "VERCEL_URL", "VERCEL_PROJECT_ID"),
        "files": ("vercel.json",),
        "capabilities": ["deployment_context", "build_environment", "preview_deployments"],
        "integration": "Use Vercel CLI/API only when installed and explicitly authorized; use scoped project tokens from the host secret manager.",
        "docs": "https://vercel.com/docs",
    },
    {
        "id": "replit",
        "label": "Replit",
        "markers": ("REPL_ID", "REPLIT_DB_URL", "REPLIT_DEPLOYMENT"),
        "files": (".replit", "replit.nix"),
        "capabilities": ["workspace_context", "hosted_runtime", "deployment_context"],
        "integration": "Use the current workspace and documented Replit APIs; never assume shell, filesystem, or deployment permissions.",
        "docs": "https://docs.replit.com/",
    },
    {
        "id": "lovable",
        "label": "Lovable",
        "markers": ("LOVABLE", "LOVABLE_PROJECT_ID"),
        "files": (),
        "capabilities": ["project_context"],
        "integration": "Treat Lovable as a project-authoring environment; use its documented GitHub sync and connected integrations rather than assuming a runtime API.",
        "docs": "https://docs.lovable.dev/",
    },
    {
        "id": "render",
        "label": "Render",
        "markers": ("RENDER", "RENDER_SERVICE_ID", "RENDER_GIT_COMMIT"),
        "files": ("render.yaml",),
        "capabilities": ["deployment_context", "runtime_environment"],
        "integration": "Use Render environment metadata and authorized APIs; do not expose environment values in diagnostics.",
        "docs": "https://render.com/docs",
    },
    {
        "id": "bolt",
        "label": "Bolt.new",
        "markers": ("BOLT", "BOLT_PROJECT_ID"),
        "files": (),
        "capabilities": ["github_import", "interactive_app_preview", "browser_ide"],
        "integration": "Use the official Bolt workspace to import a GitHub repository and preview the app; do not assume an undocumented deployment API.",
        "docs": "https://support.bolt.new/building/quickstart",
    },
    {
        "id": "v0",
        "label": "v0 by Vercel",
        "markers": ("V0", "V0_PROJECT_ID"),
        "files": (),
        "capabilities": ["github_import", "sandbox_preview", "agentic_code_editing"],
        "integration": "Import the repository through v0 Git Import; preview runs in its isolated sandbox. Deployment remains a separate user-authorized action.",
        "docs": "https://v0.app/docs/git-import",
    },
    {
        "id": "stackblitz",
        "label": "StackBlitz",
        "markers": ("STACKBLITZ",),
        "files": (),
        "capabilities": ["github_import", "webcontainer_preview", "browser_ide"],
        "integration": "Use a repository launch URL for supported GitHub projects; preview depends on framework compatibility and dependencies.",
        "docs": "https://developer.stackblitz.com/guides/user-guide/available-environments",
    },
    {
        "id": "codesandbox",
        "label": "CodeSandbox",
        "markers": ("CODESANDBOX",),
        "files": (),
        "capabilities": ["github_import", "sandbox_preview", "browser_ide"],
        "integration": "Import the GitHub repository in CodeSandbox; runtime/preview availability depends on the project and provider account.",
        "docs": "https://codesandbox.io/",
    },
    {
        "id": "railway",
        "label": "Railway",
        "markers": ("RAILWAY_ENVIRONMENT_ID", "RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_ID"),
        "files": ("railway.json", "railway.toml"),
        "capabilities": ["isolated_sandboxes", "preview_domains", "runtime_execution"],
        "integration": "Use Railway's documented sandbox SDK/API only with owner-configured credentials and environment scope; sandbox creation can incur resource use.",
        "docs": "https://docs.railway.com/sandboxes",
    },
    {
        "id": "codespaces",
        "label": "GitHub Codespaces",
        "markers": ("CODESPACES", "CODESPACE_NAME", "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN"),
        "files": (".devcontainer/devcontainer.json",),
        "capabilities": ["workspace_context", "development_container", "port_forwarding_context"],
        "integration": "Use the current workspace and user-authorized GitHub permissions; never assume repository write access.",
        "docs": "https://docs.github.com/en/codespaces",
    },
)

_COMMON_CAPABILITIES = {
    "python": ["python_runtime"],
    "node": ["node_runtime", "javascript_tooling"],
    "package.json": ["node_project"],
    "requirements.txt": ["python_project"],
    "pyproject.toml": ["python_project"],
    "Dockerfile": ["container_build_context"],
    "docker-compose.yml": ["multi_service_context"],
    "compose.yml": ["multi_service_context"],
    ".git": ["source_control_metadata"],
}


def inspect_agent_environment(
    environ: Mapping[str, str] | None = None,
    project_root: str | os.PathLike[str] | None = None,
    marker_files: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Return a bounded, secret-safe runtime and provider capability report."""
    env = os.environ if environ is None else environ
    env_names = {str(name).upper() for name in env.keys()}
    root = Path(project_root or Path.cwd())
    if marker_files is None:
        try:
            markers = {child.name for child in root.iterdir() if child.is_file() or child.is_dir()}
        except OSError:
            markers = set()
    else:
        markers = {str(name) for name in marker_files}

    detected: list[dict[str, Any]] = []
    for provider in _PROVIDERS:
        matched_env = sorted(name for name in provider["markers"] if name in env_names)
        matched_files = sorted(name for name in provider["files"] if name in markers)
        if matched_env or matched_files:
            detected.append({
                "id": provider["id"],
                "label": provider["label"],
                "confidence": "high" if matched_env else "marker_only",
                "signals": {
                    "environment_variable_names": matched_env,
                    "project_markers": matched_files,
                },
                "capabilities": list(provider["capabilities"]),
                "integration_guidance": provider["integration"],
                "documentation": provider["docs"],
            })

    common: set[str] = set()
    for marker, capabilities in _COMMON_CAPABILITIES.items():
        if marker in markers or marker.upper() in env_names:
            common.update(capabilities)

    if not detected:
        detected.append({
            "id": "generic",
            "label": "Generic agent runtime",
            "confidence": "fallback",
            "signals": {"environment_variable_names": [], "project_markers": []},
            "capabilities": [],
            "integration_guidance": "Use only capabilities confirmed by local probes and explicitly granted permissions.",
            "documentation": None,
        })

    return {
        "schema_version": 1,
        "status": "detected",
        "providers": detected,
        "common_capabilities": sorted(common),
        "security": {
            "environment_values_read": False,
            "secrets_returned": False,
            "external_resources_modified": False,
            "automatic_deployment_performed": False,
        },
        "ownership_model": {
            "workspace": "Operate within the current workspace only when its access is confirmed.",
            "external_accounts": "Never claim, adopt, or modify an external account or project without explicit authorization and provider-scoped credentials.",
            "persistence": "Offer an explicit, reviewable setup plan for durable memory, backups, and integrations; do not copy secrets or private data by default.",
        },
        "limitations": [
            "Provider detection is heuristic and does not prove that a provider API, CLI, deployment permission, or network route is usable.",
            "Environment variables are inspected by name only; their values are never returned.",
            "Provider capabilities must be verified with a bounded, read-only probe before use.",
        ],
    }
