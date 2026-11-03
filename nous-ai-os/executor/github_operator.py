"""NOUS GitHub & Pages Operator — Repository inspection, code modifications, and GitHub Pages deployments."""
from __future__ import annotations

import base64
import json
import os
import re
import threading
from pathlib import Path
from typing import Any

import requests

GITHUB_API_BASE = "https://api.github.com"
CONFIG_PATH = Path(os.environ.get("NOUS_DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "github_config.json"
MAX_FILE_BYTES = 1_000_000  # 1MB limit for in-memory code editing
REQUEST_TIMEOUT = (5, 20)
_LOCK = threading.RLock()

MISSING_TOKEN_MESSAGE = "Δεν έχει οριστεί GitHub Token. Πρόσθεσε ένα Personal Access Token στις ρυθμίσεις."
_APP_SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
_SKIP_PARTS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
_DENY_NAMES = {
    ".env", ".npmrc", ".pypirc", ".netrc", "secrets.json", "credentials.json",
    "github_config.json", "id_rsa", "id_ed25519", "id_ecdsa",
}
_DENY_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".db", ".sqlite", ".sqlite3"}
_TOKEN_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"(?i)(bearer\s+)[^\s,;\"']+"),
    re.compile(r"(?i)(authorization['\"]?\s*[:=]\s*['\"]?)[^\s,;\"']+"),
)


def redact_secrets(value: Any, token: str | None = None) -> Any:
    """Remove GitHub credentials from text/structures before returning or logging them."""
    if isinstance(value, str):
        text = value
        known = token if token is not None else get_github_token()
        if known and len(known) >= 4:
            text = text.replace(known, "[REDACTED]")
        for pattern in _TOKEN_PATTERNS:
            text = pattern.sub(lambda m: (m.group(1) if m.groups() else "") + "[REDACTED]", text)
        return text
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if isinstance(k, str) and k.lower() in {"token", "authorization", "access_token"} else redact_secrets(v, token))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(v, token) for v in value]
    return value


def _missing_token(action: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": "missing_token",
        "token_required": True,
        "action": action,
        "message": MISSING_TOKEN_MESSAGE,
    }


def _safe_error(exc: Exception, token: str | None = None) -> str:
    return redact_secrets(f"{type(exc).__name__}: {exc}", token)[:300]


def get_token_source() -> str | None:
    """Report where the token comes from ("config"/"env") without revealing it."""
    with _LOCK:
        if CONFIG_PATH.exists():
            try:
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                if str(cfg.get("token", "")).strip():
                    return "config"
            except Exception:
                pass
    if os.environ.get("GITHUB_TOKEN", "").strip() or os.environ.get("GITHUB_PAT", "").strip():
        return "env"
    return None


def get_github_token() -> str:
    """Retrieve GitHub token from config file or environment."""
    with _LOCK:
        if CONFIG_PATH.exists():
            try:
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                tok = cfg.get("token", "").strip()
                if tok:
                    return tok
            except Exception:
                pass
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        token = os.environ.get("GITHUB_PAT", "").strip()
    return token


def save_github_config(token: str, default_owner: str | None = None) -> dict[str, Any]:
    """Save GitHub credentials securely with 0600 permissions."""
    token = (token or "").strip() if isinstance(token, str) else ""
    if any(ch.isspace() for ch in token) or len(token) > 512:
        return {"ok": False, "error": "invalid_token_format", "has_token": False}
    if default_owner is not None and not isinstance(default_owner, str):
        default_owner = None
    with _LOCK:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {"token": token}
        if default_owner:
            data["default_owner"] = default_owner.strip()
        temp = CONFIG_PATH.with_suffix(".tmp")
        temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass
        os.replace(temp, CONFIG_PATH)
    return {"ok": True, "has_token": bool(token), "default_owner": default_owner}


def get_default_owner() -> str:
    """Get configured default owner or fallback to traianos1985-glitch."""
    with _LOCK:
        if CONFIG_PATH.exists():
            try:
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                owner = cfg.get("default_owner", "").strip()
                if owner:
                    return owner
            except Exception:
                pass
    return os.environ.get("GITHUB_OWNER", "traianos1985-glitch").strip()


def _headers(token: str | None = None) -> dict[str, str]:
    tok = token or get_github_token()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "NOUS-AI-OS-GitHub-Operator/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return headers


def get_github_status(token: str | None = None) -> dict[str, Any]:
    """Check connectivity and scopes with GitHub API."""
    tok = token or get_github_token()
    source = "argument" if token else get_token_source()
    if not tok:
        return {
            "ok": True,
            "connected": False,
            "token_configured": False,
            "token_source": None,
            "error": "missing_token",
            "message": MISSING_TOKEN_MESSAGE,
            "default_owner": get_default_owner(),
        }

    try:
        res = requests.get(f"{GITHUB_API_BASE}/user", headers=_headers(tok), timeout=REQUEST_TIMEOUT)
        if res.status_code == 200:
            user_data = res.json()
            scopes_header = res.headers.get("X-OAuth-Scopes", "")
            scopes = [s.strip() for s in scopes_header.split(",") if s.strip()]
            remaining = int(res.headers.get("X-RateLimit-Remaining", "-1"))
            return {
                "ok": True,
                "connected": True,
                "token_configured": True,
                "token_source": source,
                "login": user_data.get("login"),
                "name": user_data.get("name"),
                "avatar_url": user_data.get("avatar_url"),
                "html_url": user_data.get("html_url"),
                "public_repos": user_data.get("public_repos", 0),
                "total_private_repos": user_data.get("total_private_repos", 0),
                "scopes": scopes,
                "rate_limit_remaining": remaining,
                "default_owner": user_data.get("login") or get_default_owner(),
            }
        elif res.status_code == 401:
            return {
                "ok": False,
                "connected": False,
                "status_code": 401,
                "token_configured": True,
                "token_source": source,
                "default_owner": get_default_owner(),
                "error": "invalid_credentials",
                "message": "Το GitHub Token είναι άκυρο ή έχει λήξει.",
            }
        else:
            return {
                "ok": False,
                "connected": False,
                "status_code": res.status_code,
                "token_configured": True,
                "token_source": source,
                "error": f"github_http_{res.status_code}",
                "message": f"GitHub API error: {res.status_code}",
            }
    except Exception as exc:
        return {
            "ok": False,
            "connected": False,
            "token_configured": True,
            "token_source": source,
            "error": "network_error",
            "message": f"Αποτυχία σύνδεσης με GitHub: {_safe_error(exc, tok)}",
        }


def list_repositories(per_page: int = 50, sort: str = "updated") -> dict[str, Any]:
    """List repositories of the authenticated user or configured default owner."""
    tok = get_github_token()
    headers = _headers(tok)
    try:
        url = f"{GITHUB_API_BASE}/user/repos?sort={sort}&per_page={min(per_page, 100)}&affiliation=owner,collaborator"
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        # If /user/repos fails due to token scope or anonymous, fallback to public repos of default owner
        if res.status_code != 200:
            owner = get_default_owner()
            fallback_url = f"{GITHUB_API_BASE}/users/{owner}/repos?sort={sort}&per_page={min(per_page, 100)}"
            res = requests.get(fallback_url, headers=headers, timeout=REQUEST_TIMEOUT)

        if res.status_code != 200:
            return {
                "ok": False,
                "status_code": res.status_code,
                "error": f"github_http_{res.status_code}",
                "repositories": [],
                "anonymous": not tok,
            }

        repos_raw = res.json()
        if not isinstance(repos_raw, list):
            return {"ok": False, "error": "invalid_payload", "repositories": []}

        repos = []
        for r in repos_raw:
            owner_login = r.get("owner", {}).get("login", "")
            repo_name = r.get("name", "")
            has_pages = bool(r.get("has_pages"))
            pages_url = f"https://{owner_login}.github.io/{repo_name}/" if has_pages else None
            repos.append({
                "id": r.get("id"),
                "name": repo_name,
                "full_name": r.get("full_name"),
                "owner": owner_login,
                "html_url": r.get("html_url"),
                "description": r.get("description") or "",
                "default_branch": r.get("default_branch", "main"),
                "visibility": r.get("visibility", "public"),
                "updated_at": r.get("updated_at"),
                "has_pages": has_pages,
                "pages_url": pages_url,
                "language": r.get("language"),
                "stars": r.get("stargazers_count", 0),
                "open_issues": r.get("open_issues_count", 0),
                "archived": bool(r.get("archived")),
            })

        return {"ok": True, "count": len(repos), "repositories": repos, "anonymous": not tok}
    except Exception as exc:
        return {"ok": False, "error": _safe_error(exc, tok), "repositories": [], "anonymous": not tok}


def get_repository_tree(owner: str, repo: str, path: str = "", branch: str | None = None) -> dict[str, Any]:
    """List directory contents for a specific repo path."""
    headers = _headers()
    clean_path = path.strip("/")
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{clean_path}"
    params = {}
    if branch:
        params["ref"] = branch

    try:
        res = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        if res.status_code != 200:
            return {"ok": False, "status_code": res.status_code, "error": f"github_http_{res.status_code}", "items": []}

        data = res.json()
        if not isinstance(data, list):
            # Single file returned
            return {
                "ok": True,
                "is_file": True,
                "items": [{
                    "name": data.get("name"),
                    "path": data.get("path"),
                    "type": data.get("type"),
                    "size": data.get("size"),
                    "sha": data.get("sha"),
                    "html_url": data.get("html_url"),
                }],
            }

        items = []
        for it in data:
            items.append({
                "name": it.get("name"),
                "path": it.get("path"),
                "type": it.get("type"),  # "file" or "dir"
                "size": it.get("size", 0),
                "sha": it.get("sha"),
                "html_url": it.get("html_url"),
            })
        items.sort(key=lambda x: (0 if x["type"] == "dir" else 1, x["name"].lower()))
        return {"ok": True, "is_file": False, "path": clean_path, "count": len(items), "items": items}
    except Exception as exc:
        return {"ok": False, "error": _safe_error(exc), "items": []}


def get_file_content(owner: str, repo: str, path: str, branch: str | None = None) -> dict[str, Any]:
    """Retrieve and decode a file's content as text."""
    headers = _headers()
    clean_path = path.strip("/")
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{clean_path}"
    params = {}
    if branch:
        params["ref"] = branch

    try:
        res = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        if res.status_code != 200:
            return {"ok": False, "status_code": res.status_code, "error": f"github_http_{res.status_code}"}

        data = res.json()
        if data.get("type") != "file":
            return {"ok": False, "error": "not_a_file", "type": data.get("type")}

        size = data.get("size", 0)
        if size > MAX_FILE_BYTES:
            return {"ok": False, "error": "file_too_large", "size": size, "max_bytes": MAX_FILE_BYTES}

        raw_b64 = data.get("content", "")
        try:
            content_text = base64.b64decode(raw_b64).decode("utf-8")
        except UnicodeDecodeError:
            return {"ok": False, "error": "binary_file_not_text", "size": size}

        return {
            "ok": True,
            "name": data.get("name"),
            "path": data.get("path"),
            "sha": data.get("sha"),
            "size": size,
            "content": content_text,
            "html_url": data.get("html_url"),
        }
    except Exception as exc:
        return {"ok": False, "error": _safe_error(exc)}


def commit_file(
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str,
    branch: str | None = None,
    sha: str | None = None,
) -> dict[str, Any]:
    """Commit a single file modification or creation via GitHub Contents API."""
    tok = get_github_token()
    if not tok:
        return _missing_token("commit")

    headers = _headers(tok)
    clean_path = path.strip("/")
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{clean_path}"

    # If sha is not provided, look it up to support update
    current_sha = sha
    if not current_sha:
        lookup = get_file_content(owner, repo, clean_path, branch=branch)
        if lookup.get("ok"):
            current_sha = lookup.get("sha")

    b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload: dict[str, Any] = {
        "message": message or f"update: {clean_path} via NOUS AI OS",
        "content": b64_content,
    }
    if current_sha:
        payload["sha"] = current_sha
    if branch:
        payload["branch"] = branch

    try:
        res = requests.put(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        if res.status_code in (200, 201):
            data = res.json()
            commit_info = data.get("commit", {})
            return {
                "ok": True,
                "status_code": res.status_code,
                "commit_sha": commit_info.get("sha"),
                "commit_url": commit_info.get("html_url"),
                "path": clean_path,
                "content_sha": data.get("content", {}).get("sha"),
                "message": payload["message"],
            }
        else:
            try:
                err_body = res.json() if res.text else {}
            except ValueError:
                err_body = {}
            message = err_body.get("message") if isinstance(err_body, dict) else None
            return {
                "ok": False,
                "status_code": res.status_code,
                "error": redact_secrets(str(message or f"github_http_{res.status_code}"), tok)[:300],
            }
    except Exception as exc:
        return {"ok": False, "error": _safe_error(exc, tok)}


def create_or_update_pages_app(
    repo_name: str,
    files: dict[str, str],
    description: str = "Deployed by NOUS AI OS",
    is_private: bool = False,
    enable_pages: bool = True,
) -> dict[str, Any]:
    """Create a new GitHub repository, upload files, and activate GitHub Pages."""
    tok = get_github_token()
    if not tok:
        return _missing_token("deploy_pages")

    clean_name = re.sub(r"[^A-Za-z0-9_.-]", "-", (repo_name or "").strip()).strip("-.")
    if not clean_name:
        return {"ok": False, "error": "invalid_repo_name"}
    if not isinstance(files, dict) or not files:
        return {"ok": False, "error": "no_files"}
    for fpath, fcontent in files.items():
        if not isinstance(fpath, str) or not isinstance(fcontent, str):
            return {"ok": False, "error": "invalid_file_entry"}
        parts = fpath.replace("\\", "/").split("/")
        if fpath.startswith("/") or ".." in parts or not fpath.strip():
            return {"ok": False, "error": "unsafe_file_path", "path": fpath[:200]}
        if _is_sensitive_file(Path(fpath)):
            return {"ok": False, "error": "sensitive_file_blocked", "path": fpath[:200]}

    headers = _headers(tok)
    owner = get_default_owner()
    try:
        check_res = requests.get(f"{GITHUB_API_BASE}/repos/{owner}/{clean_name}", headers=headers, timeout=REQUEST_TIMEOUT)
        repo_data: dict[str, Any] = {}
        if check_res.status_code == 404:
            create_payload = {
                "name": clean_name,
                "description": description,
                "private": is_private,
                "auto_init": True,  # initializes with README.md so main branch exists
            }
            create_res = requests.post(f"{GITHUB_API_BASE}/user/repos", headers=headers, json=create_payload, timeout=REQUEST_TIMEOUT)
            if create_res.status_code not in (200, 201):
                return {
                    "ok": False,
                    "error": "create_repo_failed",
                    "status_code": create_res.status_code,
                }
            repo_data = create_res.json()
        elif check_res.status_code == 200:
            repo_data = check_res.json()
        elif check_res.status_code == 401:
            return {"ok": False, "error": "invalid_credentials", "status_code": 401, "message": "Το GitHub Token είναι άκυρο ή έχει λήξει."}
        else:
            return {"ok": False, "error": f"repo_check_failed_{check_res.status_code}", "status_code": check_res.status_code}
    except Exception as exc:
        return {"ok": False, "error": "network_error", "message": _safe_error(exc, tok)}

    owner = (repo_data.get("owner") or {}).get("login", owner)
    default_branch = repo_data.get("default_branch", "main")

    committed: list[str] = []
    failed: list[dict[str, str]] = []
    for fpath, fcontent in files.items():
        res = commit_file(
            owner=owner,
            repo=clean_name,
            path=fpath,
            content=fcontent,
            message=f"deploy: add {fpath} via NOUS AI OS",
            branch=default_branch,
        )
        if res.get("ok"):
            committed.append(fpath)
        else:
            failed.append({"path": fpath, "error": str(res.get("error", "commit_failed"))[:200]})

    pages_enabled = False
    pages_error: str | None = None
    pages_url = f"https://{owner}.github.io/{clean_name}/"
    if enable_pages and committed:
        try:
            pres = requests.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{clean_name}/pages",
                headers=headers,
                json={"source": {"branch": default_branch, "path": "/"}},
                timeout=REQUEST_TIMEOUT,
            )
            if pres.status_code in (200, 201, 409):  # 409 means already enabled
                pages_enabled = True
            else:
                pages_error = f"github_http_{pres.status_code}"
        except Exception as exc:
            pages_error = _safe_error(exc, tok)

    ok = bool(committed) and not failed and (pages_enabled or not enable_pages)
    return {
        "ok": ok,
        "partial": bool(committed) and not ok,
        "error": None if ok else ("commit_failed" if failed or not committed else "pages_enable_failed"),
        "repo_name": clean_name,
        "owner": owner,
        "repo_url": repo_data.get("html_url") or f"https://github.com/{owner}/{clean_name}",
        "pages_enabled": pages_enabled,
        "pages_error": pages_error,
        "pages_url": pages_url,
        "committed_files": committed,
        "failed_files": failed,
    }


def _apps_root() -> Path:
    return Path(os.environ.get("NOUS_DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "generated_apps"


def _is_sensitive_file(path: Path) -> bool:
    name = path.name.lower()
    return (
        name in _DENY_NAMES
        or name.startswith(".env")
        or path.suffix.lower() in _DENY_SUFFIXES
        or any(part in _SKIP_PARTS for part in path.parts)
    )


def collect_sandbox_app_files(app_name: str) -> dict[str, Any]:
    """Collect publishable files of a generated app; never follow symlinks or include secrets."""
    if not isinstance(app_name, str) or not _APP_SLUG.fullmatch(app_name) or ".." in app_name:
        return {"ok": False, "error": "invalid_app_name"}
    root = _apps_root().resolve()
    app_dir = (root / app_name).resolve()
    if root not in app_dir.parents:
        return {"ok": False, "error": "path_outside_apps_directory"}
    if not app_dir.is_dir():
        return {"ok": False, "error": "app_not_found", "message": f"Η εφαρμογή '{app_name}' δεν βρέθηκε στο generated_apps."}

    files: dict[str, str] = {}
    excluded: list[dict[str, str]] = []
    for p in sorted(app_dir.rglob("*")):
        rel_path = p.relative_to(app_dir)
        rel = rel_path.as_posix()
        if p.is_symlink():
            excluded.append({"path": rel, "reason": "symlink"})
            continue
        if not p.is_file():
            continue
        if _is_sensitive_file(rel_path):
            excluded.append({"path": rel, "reason": "sensitive"})
            continue
        if p.stat().st_size > MAX_FILE_BYTES:
            excluded.append({"path": rel, "reason": "too_large"})
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            excluded.append({"path": rel, "reason": "not_text"})
            continue
        if any(pattern.search(text) for pattern in _TOKEN_PATTERNS[:2]):
            excluded.append({"path": rel, "reason": "contains_credentials"})
            continue
        files[rel] = text

    if not files:
        return {"ok": False, "error": "empty_app", "message": "Δεν βρέθηκαν αρχεία προς δημοσίευση.", "excluded_files": excluded}
    return {"ok": True, "files": files, "excluded_files": excluded}


def deploy_sandbox_app_to_github(
    app_name: str,
    repo_name: str | None = None,
    description: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Publish data/generated_apps/{app_name} to GitHub Pages, or preview the publish plan."""
    collected = collect_sandbox_app_files(app_name)
    if not collected.get("ok"):
        return collected
    files: dict[str, str] = collected["files"]
    target_repo = re.sub(r"[^A-Za-z0-9_.-]", "-", (repo_name or app_name).strip()).strip("-.")
    if dry_run:
        has_token = bool(get_github_token())
        owner = get_default_owner()
        return {
            "ok": True,
            "dry_run": True,
            "token_configured": has_token,
            "ready": has_token and bool(target_repo),
            "message": None if has_token else MISSING_TOKEN_MESSAGE,
            "repo_name": target_repo,
            "owner": owner,
            "pages_url": f"https://{owner}.github.io/{target_repo}/",
            "files": sorted(files),
            "total_bytes": sum(len(v.encode("utf-8")) for v in files.values()),
            "excluded_files": collected["excluded_files"],
        }
    if not get_github_token():
        return _missing_token("deploy_pages")
    desc = description or f"NOUS AI OS App: {app_name}"
    result = create_or_update_pages_app(repo_name=target_repo, files=files, description=desc, enable_pages=True)
    result["excluded_files"] = collected["excluded_files"]
    return result


_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")


def _valid_repo(owner: str, repo: str) -> bool:
    return bool(_NAME.fullmatch(owner or "")) and bool(_NAME.fullmatch(repo or ""))


def search_code(owner: str, repo: str, query: str, limit: int = 10) -> dict[str, Any]:
    """Read-only code search inside one repository (GitHub code search needs a token)."""
    if not _valid_repo(owner, repo):
        return {"ok": False, "error": "invalid_repository"}
    query = (query or "").strip()
    if not query or len(query) > 200:
        return {"ok": False, "error": "invalid_query"}
    tok = get_github_token()
    if not tok:
        return _missing_token("search_code")
    try:
        res = requests.get(
            f"{GITHUB_API_BASE}/search/code",
            headers=_headers(tok),
            params={"q": f"{query} repo:{owner}/{repo}", "per_page": max(1, min(limit, 30))},
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code != 200:
            return {"ok": False, "status_code": res.status_code, "error": f"github_http_{res.status_code}"}
        items = res.json().get("items") or []
        return {
            "ok": True,
            "total_count": res.json().get("total_count", len(items)),
            "items": [{"path": i.get("path"), "html_url": i.get("html_url")} for i in items[:limit]],
        }
    except Exception as exc:
        return {"ok": False, "error": _safe_error(exc, tok)}


def get_pages_status(owner: str, repo: str) -> dict[str, Any]:
    """Read-only GitHub Pages deployment status for one repository."""
    if not _valid_repo(owner, repo):
        return {"ok": False, "error": "invalid_repository"}
    tok = get_github_token()
    try:
        res = requests.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pages", headers=_headers(tok), timeout=REQUEST_TIMEOUT)
        if res.status_code == 404:
            return {"ok": True, "pages_enabled": False}
        if res.status_code != 200:
            return {"ok": False, "status_code": res.status_code, "error": f"github_http_{res.status_code}"}
        data = res.json()
        return {"ok": True, "pages_enabled": True, "status": data.get("status"), "url": data.get("html_url"),
                "build_type": data.get("build_type")}
    except Exception as exc:
        return {"ok": False, "error": _safe_error(exc, tok)}
