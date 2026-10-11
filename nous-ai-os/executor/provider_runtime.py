"""Bounded, secret-safe probes and explicitly authorized provider operations."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from executor.agent_environment_adapters import inspect_agent_environment

_PROVIDER_LABELS = {
    "vercel": "Vercel", "render": "Render", "replit": "Replit",
    "lovable": "Lovable", "codespaces": "GitHub Codespaces", "generic": "Generic runtime",
    "bolt": "Bolt.new", "v0": "v0 by Vercel", "stackblitz": "StackBlitz",
    "codesandbox": "CodeSandbox", "railway": "Railway",
}
_DOCS = {
    "vercel": "https://vercel.com/docs", "render": "https://render.com/docs",
    "replit": "https://docs.replit.com/", "lovable": "https://docs.lovable.dev/",
    "codespaces": "https://docs.github.com/en/codespaces",
    "bolt": "https://support.bolt.new/building/quickstart",
    "v0": "https://v0.app/docs/git-import",
    "stackblitz": "https://developer.stackblitz.com/guides/user-guide/available-environments",
    "codesandbox": "https://codesandbox.io/",
    "railway": "https://docs.railway.com/sandboxes",
}


def workspace_root() -> Path:
    configured = os.environ.get("NOUS_WORKSPACE_ROOT", "").strip()
    return Path(configured or Path.cwd()).expanduser().resolve()


def _resolve_workspace_path(value: Any) -> Path:
    root = workspace_root()
    raw = str(value or ".").strip()
    candidate = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("project_path_outside_workspace") from exc
    if not candidate.exists() or not candidate.is_dir():
        raise ValueError("project_path_not_found")
    return candidate


def provider_inventory() -> dict[str, Any]:
    root = workspace_root()
    report = inspect_agent_environment(project_root=root)
    detected_ids = {item["id"] for item in report.get("providers", [])}
    env_names = set(os.environ)
    providers = []
    for provider_id, label in _PROVIDER_LABELS.items():
        if provider_id == "generic":
            continue
        cli = shutil.which("vercel") if provider_id == "vercel" else None
        configured = (
            provider_id == "vercel" and bool(cli or "VERCEL_TOKEN" in env_names)
        ) or (
            provider_id == "render" and "RENDER_API_KEY" in env_names and "RENDER_SERVICE_ID" in env_names
        ) or provider_id in {"replit", "lovable", "codespaces"}
        operation = {
            "vercel": "probe_and_deploy", "render": "probe_and_deploy",
            "replit": "workspace_probe", "lovable": "git_sync_probe",
            "codespaces": "workspace_probe",
            "bolt": "github_preview_launcher", "v0": "github_preview_launcher",
            "stackblitz": "github_preview_launcher", "codesandbox": "github_preview_launcher",
            "railway": "sandbox_preview_documentation",
        }[provider_id]
        providers.append({
            "id": provider_id, "label": label, "detected": provider_id in detected_ids,
            "configured": bool(configured), "cli_installed": bool(cli) if provider_id == "vercel" else None,
            "operation": operation,
            "requires_explicit_deploy_confirmation": provider_id in {"vercel", "render"},
            "documentation": _DOCS[provider_id],
        })
    return {
        "ok": True, "workspace": str(root), "environment": report, "providers": providers,
        "deployable_providers": ["vercel", "render"], "preview_providers": ["stackblitz", "codesandbox", "v0", "bolt"],
        "notes": [
            "Detection is not proof of permission or connectivity.",
            "Provider credentials are used only by the relevant operation and are never returned.",
            "Deployments require an authenticated NOUS request and the exact confirmation phrase DEPLOY.",
            "Lovable and Replit expose workspace/Git context only; no unsupported deploy API is assumed.",
            "Browser preview launchers open provider UIs; they do not claim a remote sandbox has started.",
            "Railway sandbox provisioning is documented but is not triggered by this preview launcher.",
        ],
    }


def _run_cli(args: list[str], cwd: Path, timeout: int = 12) -> dict[str, Any]:
    try:
        result = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, check=False)
        return {"available": True, "ok": result.returncode == 0, "returncode": result.returncode,
                "stdout": result.stdout or "", "stderr": result.stderr or ""}
    except FileNotFoundError:
        return {"available": False, "ok": False, "error": "cli_not_installed"}
    except subprocess.TimeoutExpired:
        return {"available": True, "ok": False, "error": "probe_timeout"}
    except OSError:
        return {"available": True, "ok": False, "error": "probe_failed"}


def _render_request(method: str, path: str, timeout: int = 12) -> dict[str, Any]:
    token = os.environ.get("RENDER_API_KEY", "").strip()
    if not token:
        return {"ok": False, "configured": False, "error": "render_api_key_not_configured"}
    request = urllib.request.Request(
        "https://api.render.com" + path,
        data=b'{"clearCache":"do_not_clear"}' if method == "POST" else None,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json",
                 "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(65536)
            parsed = json.loads(body.decode("utf-8")) if body else {}
            return {"ok": 200 <= response.status < 300, "configured": True,
                    "status_code": response.status, "data": parsed}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "configured": True, "status_code": exc.code,
                "error": "render_api_rejected_request"}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return {"ok": False, "configured": True, "error": "render_api_unreachable_or_invalid_response"}


def _vercel_api_probe(timeout: int = 12) -> dict[str, Any]:
    token = os.environ.get("VERCEL_TOKEN", "").strip()
    if not token:
        return {"ok": False, "configured": False, "error": "vercel_token_not_configured"}
    request = urllib.request.Request(
        "https://api.vercel.com/v9/projects?limit=1",
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(65536)
            parsed = json.loads(body.decode("utf-8")) if body else {}
            projects = parsed.get("projects", []) if isinstance(parsed, dict) else []
            return {"ok": 200 <= response.status < 300, "configured": True,
                    "status_code": response.status,
                    "projects_visible": len(projects) if isinstance(projects, list) else None}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "configured": True, "status_code": exc.code,
                "error": "vercel_api_rejected_request"}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return {"ok": False, "configured": True, "error": "vercel_api_unreachable_or_invalid_response"}


def probe_provider(provider: str) -> dict[str, Any]:
    provider_id = str(provider or "").strip().lower()
    if provider_id not in _PROVIDER_LABELS:
        return {"ok": False, "error": "unsupported_provider"}
    root = workspace_root()
    result: dict[str, Any] = {"ok": True, "provider": provider_id, "label": _PROVIDER_LABELS[provider_id]}
    if provider_id == "vercel":
        cli = shutil.which("vercel")
        if cli:
            version = _run_cli([cli, "--version"], root)
            identity = _run_cli([cli, "whoami"], root)
            result.update({"method": "vercel_cli", "cli_installed": True,
                           "version_check_ok": version["ok"], "authenticated": identity["ok"]})
            if not identity["ok"] and os.environ.get("VERCEL_TOKEN", "").strip():
                api_probe = _vercel_api_probe()
                result.update({"method": "vercel_api_fallback", "authenticated": bool(api_probe.get("ok")),
                               "status_code": api_probe.get("status_code"),
                               "projects_visible": api_probe.get("projects_visible"),
                               "error": api_probe.get("error")})
        elif os.environ.get("VERCEL_TOKEN", "").strip():
            api_probe = _vercel_api_probe()
            result.update({"method": "vercel_api", "cli_installed": False,
                           "authenticated": bool(api_probe.get("ok")),
                           "status_code": api_probe.get("status_code"),
                           "projects_visible": api_probe.get("projects_visible"),
                           "error": api_probe.get("error")})
        else:
            result.update({"method": "vercel_cli", "cli_installed": False, "authenticated": False,
                           "error": "vercel_cli_and_token_not_configured"})
    elif provider_id == "render":
        probe = _render_request("GET", "/v1/services?limit=1")
        result.update({"method": "render_api", "authenticated": bool(probe.get("ok")),
                       "status_code": probe.get("status_code"), "error": probe.get("error")})
        result["services_visible"] = len(probe.get("data", [])) if isinstance(probe.get("data"), list) else None
    elif provider_id in {"replit", "codespaces"}:
        env_names = set(os.environ)
        markers = {
            "replit": bool({"REPL_ID", "REPLIT_DB_URL", "REPLIT_DEPLOYMENT"} & env_names),
            "codespaces": bool({"CODESPACES", "CODESPACE_NAME"} & env_names),
        }
        git_path = shutil.which("git")
        git = _run_cli([git_path, "rev-parse", "--is-inside-work-tree"], root) if git_path else {"ok": False}
        result.update({"method": "workspace_probe", "runtime_marker_present": markers[provider_id],
                       "workspace_exists": root.is_dir(), "git_workspace": git["ok"]})
    elif provider_id == "lovable":
        git_path = shutil.which("git")
        remote = _run_cli([git_path, "remote", "get-url", "origin"], root) if git_path else {"ok": False}
        remote_text = (remote.get("stdout") or "").strip().lower()
        result.update({"method": "git_sync_probe", "git_installed": bool(git_path),
                       "origin_configured": bool(remote["ok"]),
                       "github_origin_detected": bool(remote["ok"] and "github.com" in remote_text)})
    else:
        result.update({"method": "read_only_inventory", "workspace_exists": root.is_dir()})
    return result



def _github_repo_slug(remote_url: str) -> str | None:
    """Return only owner/repository from a GitHub remote, never credentials or arbitrary URLs."""
    value = (remote_url or "").strip()
    match = re.fullmatch(r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", value, re.IGNORECASE)
    if not match:
        return None
    owner, repo = match.group(1), match.group(2)
    if owner in {".", ".."} or repo in {".", ".."}:
        return None
    return owner + "/" + repo


def preview_catalog() -> dict[str, Any]:
    """Build safe provider launch links for preview/import; never starts external compute."""
    root = workspace_root()
    git_path = shutil.which("git")
    remote = _run_cli([git_path, "remote", "get-url", "origin"], root) if git_path else {"ok": False}
    slug = _github_repo_slug(remote.get("stdout", "")) if remote.get("ok") else None
    github_url = "https://github.com/" + slug if slug else None
    previews = [
        {
            "id": "stackblitz", "label": "StackBlitz", "kind": "direct_github_preview",
            "url": "https://stackblitz.com/github/" + slug if slug else "https://stackblitz.com/",
            "ready": bool(slug), "requires_github_repo": True,
            "description": "Άνοιγμα repository σε browser IDE με WebContainer preview όπου υποστηρίζεται.",
            "documentation": _DOCS["stackblitz"],
        },
        {
            "id": "codesandbox", "label": "CodeSandbox", "kind": "github_import_preview",
            "url": "https://codesandbox.io/p/sandbox/github/" + slug if slug else "https://codesandbox.io/",
            "ready": bool(slug), "requires_github_repo": True,
            "description": "Εισαγωγή repository σε sandbox και preview όταν υποστηρίζεται το project.",
            "documentation": _DOCS["codesandbox"],
        },
        {
            "id": "v0", "label": "v0 by Vercel", "kind": "guided_github_import",
            "url": "https://v0.app", "ready": bool(slug), "requires_github_repo": True,
            "repository_url": github_url,
            "description": "Άνοιξε το v0 και εισήγαγε το GitHub URL μέσω Git Import για sandbox preview.",
            "documentation": _DOCS["v0"],
        },
        {
            "id": "bolt", "label": "Bolt.new", "kind": "guided_github_import",
            "url": "https://bolt.new", "ready": bool(slug), "requires_github_repo": True,
            "repository_url": github_url,
            "description": "Άνοιξε το Bolt και εισήγαγε το repository από το workspace του για live preview.",
            "documentation": _DOCS["bolt"],
        },
        {
            "id": "railway", "label": "Railway Sandboxes", "kind": "guided_sandbox",
            "url": "https://docs.railway.com/sandboxes", "ready": bool(slug), "requires_github_repo": True,
            "repository_url": github_url,
            "description": "Για backend preview απαιτείται ξεχωριστή ρύθμιση Railway sandbox και credentials.",
            "documentation": _DOCS["railway"],
        },
    ]
    return {
        "ok": True, "workspace": str(root), "github_repository": github_url,
        "previews": previews,
        "notes": [
            "Opening a provider link does not guarantee a successful build or preview.",
            "Private repositories require the user to authorize the provider.",
            "No sandbox is created and no deployment is triggered by this catalog endpoint.",
        ],
    }

def deploy_provider(provider: str, project_path: str = ".", mode: str = "preview",
                    confirmation: str = "") -> dict[str, Any]:
    """Deploy only after explicit confirmation and within the configured workspace."""
    provider_id = str(provider or "").strip().lower()
    if provider_id not in {"vercel", "render"}:
        return {"ok": False, "error": "deployment_not_supported_for_provider"}
    if confirmation != "DEPLOY":
        return {"ok": False, "error": "explicit_confirmation_required"}
    if mode not in {"preview", "production"}:
        return {"ok": False, "error": "invalid_deployment_mode"}
    try:
        project = _resolve_workspace_path(project_path)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    if provider_id == "vercel":
        cli = shutil.which("vercel")
        if not cli:
            return {"ok": False, "error": "vercel_cli_not_installed"}
        identity = _run_cli([cli, "whoami"], project)
        if not identity["ok"]:
            return {"ok": False, "error": "vercel_cli_not_authenticated"}
        args = [cli, "--yes"]
        if mode == "production":
            args.append("--prod")
        run = _run_cli(args, project, timeout=300)
        combined = (run.get("stdout", "") + "\n" + run.get("stderr", ""))[:20000]
        urls = sorted(set(re.findall(r"https://[A-Za-z0-9.-]+(?:/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*)?", combined)))
        return {"ok": bool(run["ok"]), "provider": provider_id, "mode": mode,
                "project_path": str(project.relative_to(workspace_root())) or ".",
                "deployment_urls": urls[:10], "error": run.get("error") if not run["ok"] else None,
                "message": "Vercel deployment command completed." if run["ok"] else "Vercel deployment failed; raw CLI output was withheld."}

    service_id = os.environ.get("RENDER_SERVICE_ID", "").strip()
    if not service_id:
        return {"ok": False, "error": "render_service_id_not_configured"}
    if not os.environ.get("RENDER_API_KEY", "").strip():
        return {"ok": False, "error": "render_api_key_not_configured"}
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", service_id):
        return {"ok": False, "error": "invalid_render_service_id"}
    response = _render_request("POST", f"/v1/services/{service_id}/deploys")
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    return {"ok": bool(response.get("ok")), "provider": provider_id, "mode": "production",
            "service_id_configured": True, "deployment_id": data.get("id"),
            "status_code": response.get("status_code"), "error": response.get("error"),
            "message": "Render deploy requested." if response.get("ok") else "Render deploy request failed."}
