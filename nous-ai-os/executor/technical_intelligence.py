"""Evidence-based dependency and technical-release monitoring for NOUS.

This module is read-only with respect to project source and package managers:
it checks official registries and writes a bounded report, but never installs,
updates, imports, or executes a suggested package version.
"""
from __future__ import annotations

import concurrent.futures
import importlib.metadata
import json
import os
import re
import threading
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("NOUS_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
REPORT_PATH = DATA_DIR / "technical_intelligence_report.json"
HISTORY_PATH = DATA_DIR / "technical_intelligence_history.json"
MAX_SCAN_LIMIT = 60
MAX_MANIFEST_DEPENDENCIES = 120
MAX_RESPONSE_BYTES = 1_000_000
_REQUEST_TIMEOUT = (3, 5)
_LOCK = threading.RLock()
_USER_AGENT = "NOUS-Technical-Intelligence/1.0 (read-only dependency monitor)"


def _read_json(path: Path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value
    except (OSError, ValueError, TypeError):
        return default


def _atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _normalise_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower().strip()


def _version_core(value: str | None) -> tuple[int, ...] | None:
    if not isinstance(value, str):
        return None
    match = re.match(r"^[v= ]*(\d+)(?:\.(\d+))?(?:\.(\d+))?", value.strip(), re.IGNORECASE)
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def _update_kind(current: str | None, latest: str | None) -> str:
    old = _version_core(current)
    new = _version_core(latest)
    if old is None or new is None:
        return "version_unknown"
    if new == old:
        return "up_to_date"
    if new < old:
        return "current_newer_than_registry"
    if new[0] > old[0]:
        return "major_update"
    if len(new) > 1 and new[1] > old[1]:
        return "minor_update"
    return "patch_update"


def _installed_python_version(name: str) -> str | None:
    candidates = [name, re.sub(r"\[[^]]*\]", "", name)]
    aliases = {
        "beautifulsoup4": "beautifulsoup4",
        "psycopg": "psycopg",
        "psycopg-binary": "psycopg-binary",
        "python-dotenv": "python-dotenv",
    }
    normalized = _normalise_name(re.sub(r"\[[^]]*\]", "", name))
    if normalized in aliases:
        candidates.append(aliases[normalized])
    for candidate in dict.fromkeys(candidates):
        try:
            return importlib.metadata.version(candidate)
        except importlib.metadata.PackageNotFoundError:
            continue
        except (ValueError, TypeError):
            continue
    return None


def _parse_requirement(line: str) -> tuple[str, str] | None:
    raw = line.split("#", 1)[0].strip()
    if not raw or raw.startswith(("-", "git+", "http:", "https:")):
        return None
    match = re.match(r"^([A-Za-z0-9_.-]+)(?:\[[^]]+\])?\s*(.*)$", raw)
    if not match:
        return None
    return match.group(1), match.group(2).strip()


def collect_dependencies(root: Path | None = None) -> list[dict]:
    """Read direct dependencies from manifests; never executes package-manager commands."""
    root = Path(root or ROOT_DIR)
    dependencies: dict[tuple[str, str], dict] = {}
    package_json = _read_json(root / "package.json", {})
    package_lock = _read_json(root / "package-lock.json", {})
    declared = {}
    if isinstance(package_json, dict):
        for section in ("dependencies", "devDependencies", "optionalDependencies"):
            entries = package_json.get(section, {})
            if not isinstance(entries, dict):
                continue
            for name, spec in entries.items():
                declared[str(name)] = str(spec)
    lock_packages = package_lock.get("packages", {}) if isinstance(package_lock, dict) else {}
    for name, spec in sorted(declared.items()):
        lock_entry = lock_packages.get(f"node_modules/{name}", {})
        current = lock_entry.get("version") if isinstance(lock_entry, dict) else None
        dependencies[("npm", name)] = {
            "ecosystem": "npm",
            "name": name,
            "current_version": str(current) if current else None,
            "declared": spec,
            "manifest": "package.json",
            "registry_url": f"https://registry.npmjs.org/{quote(name, safe='@')}/latest",
            "package_url": f"https://www.npmjs.com/package/{quote(name, safe='@/')}",
        }

    python_files = (
        ("nous-ai-os/requirements.txt", root / "nous-ai-os" / "requirements.txt"),
        ("nous-ai-os/requirements-dev.txt", root / "nous-ai-os" / "requirements-dev.txt"),
    )
    for relative, path in python_files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            parsed = _parse_requirement(line)
            if not parsed:
                continue
            name, spec = parsed
            key = ("pypi", _normalise_name(name))
            if key in dependencies:
                if spec and spec not in dependencies[key]["declared"]:
                    dependencies[key]["declared"] += f"; {spec}"
                continue
            dependencies[key] = {
                "ecosystem": "pypi",
                "name": name,
                "current_version": _installed_python_version(name),
                "declared": spec or "unspecified",
                "manifest": relative,
                "registry_url": f"https://pypi.org/pypi/{quote(name)}/json",
                "package_url": f"https://pypi.org/project/{quote(name)}/",
            }

    return list(dependencies.values())[:MAX_MANIFEST_DEPENDENCIES]


def _read_limited_json(response: requests.Response) -> dict:
    declared_size = response.headers.get("Content-Length")
    if declared_size and declared_size.isdigit() and int(declared_size) > MAX_RESPONSE_BYTES:
        raise ValueError("registry_response_too_large")
    chunks = []
    total = 0
    for chunk in response.iter_content(chunk_size=16_384):
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_RESPONSE_BYTES:
            raise ValueError("registry_response_too_large")
        chunks.append(chunk)
    try:
        value = json.loads(b"".join(chunks).decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("invalid_registry_json") from exc
    if not isinstance(value, dict):
        raise ValueError("invalid_registry_payload")
    return value


def _fetch_latest(dependency: dict) -> dict:
    """Query a fixed official registry endpoint; no arbitrary URL is accepted."""
    ecosystem = dependency.get("ecosystem")
    if ecosystem not in {"npm", "pypi"}:
        return {"ok": False, "error": "unsupported_ecosystem"}
    expected_host = "registry.npmjs.org" if ecosystem == "npm" else "pypi.org"
    registry_url = dependency.get("registry_url", "")
    if not registry_url.startswith(f"https://{expected_host}/"):
        return {"ok": False, "error": "registry_url_not_allowed"}
    try:
        response = requests.get(
            registry_url,
            timeout=_REQUEST_TIMEOUT,
            headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
            stream=True,
            allow_redirects=False,
        )
        try:
            if response.status_code != 200:
                return {"ok": False, "error": f"registry_http_{response.status_code}"}
            payload = _read_limited_json(response)
        finally:
            response.close()
        latest = payload.get("version")
        if ecosystem == "pypi":
            info = payload.get("info")
            latest = info.get("version") if isinstance(info, dict) else None
        if not isinstance(latest, str) or not latest.strip():
            return {"ok": False, "error": "registry_version_missing"}
        return {"ok": True, "latest_version": latest.strip()}
    except (requests.RequestException, ValueError, OSError) as exc:
        # Avoid storing exception text, which may contain implementation details.
        return {"ok": False, "error": type(exc).__name__}


def _recommendation(dependency: dict, latest: str) -> dict:
    current = dependency.get("current_version")
    kind = _update_kind(current, latest)
    if kind == "major_update":
        reason = "Νέα major έκδοση· απαιτεί έλεγχο breaking changes πριν από οποιαδήποτε αναβάθμιση."
        priority = "review"
    elif kind == "minor_update":
        reason = "Νέα minor έκδοση· έλεγξε release notes και συμβατότητα."
        priority = "normal"
    elif kind == "patch_update":
        reason = "Νέα patch έκδοση· έλεγξε release notes και γνωστά θέματα."
        priority = "normal"
    elif kind == "version_unknown":
        reason = "Υπάρχει διαθέσιμη έκδοση, αλλά δεν υπάρχει αξιόπιστη τρέχουσα έκδοση για σύγκριση."
        priority = "investigate"
    elif kind == "current_newer_than_registry":
        reason = "Η τρέχουσα έκδοση φαίνεται νεότερη από το stable tag του registry."
        priority = "verify"
    else:
        reason = "Η τρέχουσα έκδοση συμφωνεί με την έκδοση του registry."
        priority = "none"
    return {
        "ecosystem": dependency["ecosystem"],
        "name": dependency["name"],
        "current_version": current,
        "latest_version": latest,
        "declared": dependency.get("declared"),
        "manifest": dependency.get("manifest"),
        "kind": kind,
        "priority": priority,
        "reason": reason,
        "source_url": dependency.get("package_url"),
        "checked_at": time.time(),
        "action": "proposal_only",
    }


def run_scan(limit: int = 40) -> dict:
    """Check official registries and persist a bounded, evidence-linked report."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_SCAN_LIMIT:
        return {
            "ok": False,
            "error": "invalid_limit",
            "allowed_range": [1, MAX_SCAN_LIMIT],
        }

    started = time.monotonic()
    dependencies = collect_dependencies()[:limit]
    findings = []
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(_fetch_latest, dependency): dependency
            for dependency in dependencies
        }
        for future in concurrent.futures.as_completed(futures):
            dependency = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"ok": False, "error": type(exc).__name__}
            if not result.get("ok"):
                errors.append({
                    "ecosystem": dependency["ecosystem"],
                    "name": dependency["name"],
                    "error": result.get("error", "registry_unavailable"),
                })
                continue
            findings.append(_recommendation(dependency, result["latest_version"]))

    findings.sort(key=lambda item: (
        {"major_update": 0, "minor_update": 1, "patch_update": 2, "version_unknown": 3,
         "current_newer_than_registry": 4, "up_to_date": 5}.get(item["kind"], 6),
        item["ecosystem"],
        item["name"].lower(),
    ))
    updates = [item for item in findings if item["kind"] in {"major_update", "minor_update", "patch_update"}]
    report = {
        "ok": bool(findings),
        "status": "complete" if not errors else ("partial" if findings else "unavailable"),
        "checked_at": time.time(),
        "duration_ms": round((time.monotonic() - started) * 1000),
        "manifest_count": len(dependencies),
        "checked_count": len(findings),
        "error_count": len(errors),
        "update_count": len(updates),
        "major_update_count": sum(item["kind"] == "major_update" for item in updates),
        "findings": findings,
        "updates": updates,
        "errors": errors[:30],
        "safety": {
            "read_only": True,
            "package_installs_performed": 0,
            "source_files_modified": 0,
            "automatic_upgrades": False,
            "registries": ["registry.npmjs.org", "pypi.org"],
        },
    }
    with _LOCK:
        _atomic_json(REPORT_PATH, report)
        history = _read_json(HISTORY_PATH, [])
        if not isinstance(history, list):
            history = []
        history.append({
            "checked_at": report["checked_at"],
            "status": report["status"],
            "manifest_count": report["manifest_count"],
            "checked_count": report["checked_count"],
            "error_count": report["error_count"],
            "update_count": report["update_count"],
            "major_update_count": report["major_update_count"],
        })
        _atomic_json(HISTORY_PATH, history[-20:])
    return report


def latest_report() -> dict:
    report = _read_json(REPORT_PATH, {})
    return report if isinstance(report, dict) else {}


def list_proposals(limit: int = 30) -> dict:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        return {"ok": False, "error": "invalid_limit", "allowed_range": [1, 100]}
    report = latest_report()
    updates = report.get("updates", [])
    if not isinstance(updates, list):
        updates = []
    return {
        "ok": True,
        "generated_at": report.get("checked_at"),
        "source_report_status": report.get("status", "not_scanned"),
        "count": min(len(updates), limit),
        "proposals": updates[:limit],
        "note": "Οι προτάσεις βασίζονται σε metadata επίσημων registries. Δεν έγινε εγκατάσταση ή αλλαγή κώδικα.",
    }


def technical_intelligence_status() -> dict:
    report = latest_report()
    history = _read_json(HISTORY_PATH, [])
    if not isinstance(history, list):
        history = []
    return {
        "ok": True,
        "service": "technical_intelligence",
        "mode": "read_only",
        "last_scan_at": report.get("checked_at"),
        "last_scan_status": report.get("status", "not_scanned"),
        "last_scan_counts": {
            "manifest_count": report.get("manifest_count", 0),
            "checked_count": report.get("checked_count", 0),
            "error_count": report.get("error_count", 0),
            "update_count": report.get("update_count", 0),
            "major_update_count": report.get("major_update_count", 0),
        },
        "history": history[-10:],
        "limits": {
            "max_scan_limit": MAX_SCAN_LIMIT,
            "max_response_bytes": MAX_RESPONSE_BYTES,
            "request_timeout_seconds": sum(_REQUEST_TIMEOUT),
        },
        "automatic_installs": False,
        "automatic_source_changes": False,
    }
