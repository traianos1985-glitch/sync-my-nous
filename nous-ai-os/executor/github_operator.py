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
        return {"ok": False, "error": "unauthorized", "message": "Απαιτείται GitHub Token για δημιουργία repo."}

    headers = _headers(tok)
    clean_name = re.sub(r"[^A-Za-z0-9_.-]", "-", repo_name.strip()).strip("-")
    if not clean_name:
        return {"ok": False, "error": "invalid_repo_name"}

    # 1. Check or create repository
    owner = get_default_owner()
    check_url = f"{GITHUB_API_BASE}/repos/{owner}/{clean_name}"
    check_res = requests.get(check_url, headers=headers, timeout=REQUEST_TIMEOUT)
    
    repo_data = {}
    if check_res.status_code == 404:
        # Create repo
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
                "details": create_res.json() if create_res.text else create_res.status_code,
            }
        repo_data = create_res.json()
        owner = repo_data.get("owner", {}).get("login", owner)
    elif check_res.status_code == 200:
        repo_data = check_res.json()
        owner = repo_data.get("owner", {}).get("login", owner)
    else:
        return {"ok": False, "error": f"repo_check_failed_{check_res.status_code}"}

    # 2. Commit each file
    committed = []
    default_branch = repo_data.get("default_branch", "main")
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

    # 3. Enable GitHub Pages if requested
    pages_enabled = False
    pages_url = f"https://{owner}.github.io/{clean_name}/"
    if enable_pages:
        pages_api = f"{GITHUB_API_BASE}/repos/{owner}/{clean_name}/pages"
        pages_payload = {"source": {"branch": default_branch, "path": "/"}}
        pres = requests.post(pages_api, headers=headers, json=pages_payload, timeout=REQUEST_TIMEOUT)
        if pres.status_code in (200, 201, 409):  # 409 means already enabled
            pages_enabled = True

    return {
        "ok": True,
        "repo_name": clean_name,
        "owner": owner,
        "repo_url": repo_data.get("html_url") or f"https://github.com/{owner}/{clean_name}",
        "pages_enabled": pages_enabled,
        "pages_url": pages_url,
        "committed_files": committed,
    }


def deploy_sandbox_app_to_github(app_name: str, repo_name: str | None = None, description: str | None = None) -> dict[str, Any]:
    """Read files from data/generated_apps/{app_name} and deploy to GitHub Pages."""
    app_dir = Path(os.environ.get("NOUS_DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "generated_apps" / app_name
    if not app_dir.exists() or not app_dir.is_dir():
        return {"ok": False, "error": "app_not_found", "message": f"Η εφαρμογή '{app_name}' δεν βρέθηκε στο generated_apps."}

    files: dict[str, str] = {}
    for p in app_dir.rglob("*"):
        if p.is_file() and p.stat().st_size <= MAX_FILE_BYTES:
            rel = str(p.relative_to(app_dir)).replace("\\", "/")
            try:
                files[rel] = p.read_text(encoding="utf-8")
            except Exception:
                pass

    if not files:
        return {"ok": False, "error": "empty_app", "message": f"Δεν βρέθηκαν αρχεία κώδικα στο {app_dir}."}

    target_repo = repo_name or app_name
    desc = description or f"NOUS AI OS App: {app_name}"
    return create_or_update_pages_app(repo_name=target_repo, files=files, description=desc, enable_pages=True)
