"""Persist generated-app repair proposals and run non-executing preflight checks."""
from __future__ import annotations

import ast
import hashlib
import json
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from executor.app_failure_diagnosis import _validate_changes

_SLUG = re.compile(r"^[a-z][a-z0-9_-]{0,59}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_ALLOWED_SUFFIXES = {
    ".py", ".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".json",
    ".toml", ".ini", ".md", ".txt", ".yml", ".yaml", ".sql",
}
_CRITICAL_NAMES = {
    "requirements.txt", "pyproject.toml", "package.json", "package-lock.json",
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
}
_MAX_PROPOSALS = 100


def _read_store(store_path: str | Path) -> list[dict[str, Any]]:
    path = Path(store_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return []
    return data if isinstance(data, list) and all(isinstance(x, dict) for x in data) else []


def _write_store(store_path: str | Path, items: list[dict[str, Any]]) -> None:
    path = Path(store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(items[-_MAX_PROPOSALS:], ensure_ascii=False, indent=2)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".repairs-", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
    temporary.replace(path)


def save_repair_proposal(
    app_name: str,
    apps_root: str | Path,
    diagnosis: dict[str, Any],
    store_path: str | Path = "data/app_builder_repairs.json",
) -> dict[str, Any]:
    """Persist only a bounded proposal and its baseline hashes; never write app files."""
    if not isinstance(app_name, str) or not _SLUG.fullmatch(app_name):
        return {"ok": False, "error": "invalid_app_name"}
    if not isinstance(diagnosis, dict) or diagnosis.get("ok") is not True:
        return {"ok": False, "error": "valid_diagnosis_required"}
    if diagnosis.get("app_name") != app_name or diagnosis.get("writes_performed") is not False:
        return {"ok": False, "error": "invalid_diagnosis_metadata"}
    reported_errors = diagnosis.get("change_validation_errors", [])
    if not isinstance(reported_errors, list) or reported_errors:
        return {"ok": False, "error": "diagnosis_contains_rejected_changes"}
    changes, errors = _validate_changes(app_name, diagnosis.get("changes", []))
    if errors:
        return {"ok": False, "error": "invalid_proposed_changes", "details": errors}
    if any(Path(item["path"]).suffix.lower() not in _ALLOWED_SUFFIXES for item in changes):
        return {"ok": False, "error": "unsupported_file_type"}
    hashes = diagnosis.get("baseline_hashes", {})
    if not isinstance(hashes, dict):
        return {"ok": False, "error": "invalid_baseline_hashes"}
    safe_hashes: dict[str, str] = {}
    for path, digest in hashes.items():
        if (
            isinstance(path, str)
            and path.startswith(app_name + "/")
            and ".." not in path.split("/")
            and isinstance(digest, str)
            and _SHA256.fullmatch(digest)
        ):
            safe_hashes[path] = digest
    project = (Path(apps_root).resolve() / app_name).resolve()
    root = Path(apps_root).resolve()
    if root not in project.parents or not project.is_dir():
        return {"ok": False, "error": "app_not_found"}
    item = {
        "repair_id": "repair_" + uuid.uuid4().hex,
        "app_name": app_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "summary": str(diagnosis.get("summary", ""))[:4000],
        "root_causes": diagnosis.get("root_causes", [])[:12]
        if isinstance(diagnosis.get("root_causes"), list) else [],
        "validation_plan": diagnosis.get("validation_plan", [])[:20]
        if isinstance(diagnosis.get("validation_plan"), list) else [],
        "risks": diagnosis.get("risks", [])[:20]
        if isinstance(diagnosis.get("risks"), list) else [],
        "changes": changes,
        "baseline_hashes": safe_hashes,
        "context_files": [
            p for p in diagnosis.get("context_files", [])
            if isinstance(p, str) and p.startswith(app_name + "/") and ".." not in p.split("/")
        ][:30] if isinstance(diagnosis.get("context_files"), list) else [],
        "status": "pending_review",
    }
    items = _read_store(store_path)
    items.append(item)
    _write_store(store_path, items)
    return {
        "ok": True,
        "repair_id": item["repair_id"],
        "app_name": app_name,
        "status": item["status"],
        "change_count": len(changes),
        "stored": True,
        "app_files_written": False,
    }


def review_repair_proposal(
    repair_id: str,
    apps_root: str | Path,
    store_path: str | Path = "data/app_builder_repairs.json",
) -> dict[str, Any]:
    """Run static checks and stale-baseline detection; never execute or apply the proposal."""
    if not isinstance(repair_id, str) or not re.fullmatch(r"repair_[a-f0-9]{32}", repair_id):
        return {"ok": False, "error": "invalid_repair_id"}
    proposal = next((x for x in _read_store(store_path) if x.get("repair_id") == repair_id), None)
    if proposal is None:
        return {"ok": False, "error": "repair_not_found"}
    app_name = proposal.get("app_name")
    if not isinstance(app_name, str) or not _SLUG.fullmatch(app_name):
        return {"ok": False, "error": "invalid_stored_app_name"}
    root = Path(apps_root).resolve()
    project = (root / app_name).resolve()
    if root not in project.parents or not project.is_dir():
        return {"ok": False, "error": "app_not_found"}

    changes, path_errors = _validate_changes(app_name, proposal.get("changes", []))
    blockers = [f"path_validation:{error}" for error in path_errors]
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []
    baseline_hashes = proposal.get("baseline_hashes", {})
    changed_paths = {item["path"] for item in changes}
    if not changes:
        blockers.append("proposal_has_no_changes")

    for item in changes:
        relative = item["path"]
        parts = relative.split("/")
        if Path(relative).suffix.lower() not in _ALLOWED_SUFFIXES:
            blockers.append(f"unsupported_file_type:{relative}")
            continue
        target = project.joinpath(*parts[1:])
        current = project
        has_symlink = False
        for part in parts[1:]:
            current = current / part
            if current.is_symlink():
                has_symlink = True
                break
        if has_symlink:
            blockers.append(f"symlink_target:{relative}")
            continue
        try:
            resolved = target.resolve()
            resolved.relative_to(project)
        except (OSError, ValueError):
            blockers.append(f"path_escape:{relative}")
            continue

        existed = target.exists()
        expected_hash = baseline_hashes.get(relative) if isinstance(baseline_hashes, dict) else None
        if existed:
            if not target.is_file():
                blockers.append(f"target_not_regular_file:{relative}")
                continue
            if not isinstance(expected_hash, str) or not _SHA256.fullmatch(expected_hash):
                blockers.append(f"baseline_missing:{relative}")
                continue
            actual_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                blockers.append(f"stale_baseline:{relative}")
                continue
        elif expected_hash:
            blockers.append(f"baseline_file_missing:{relative}")

        suffix = target.suffix.lower()
        if suffix == ".py":
            try:
                ast.parse(item["content"], filename=relative)
                checks.append({"path": relative, "check": "python_syntax", "ok": True})
            except SyntaxError as exc:
                blockers.append(f"python_syntax:{relative}:{exc.lineno or 0}")
                checks.append({"path": relative, "check": "python_syntax", "ok": False})
        elif suffix == ".json":
            try:
                json.loads(item["content"])
                checks.append({"path": relative, "check": "json_syntax", "ok": True})
            except ValueError:
                blockers.append(f"json_syntax:{relative}")
                checks.append({"path": relative, "check": "json_syntax", "ok": False})
        else:
            checks.append({"path": relative, "check": "file_type_review", "ok": True, "executed": False})

        if target.name.lower() in _CRITICAL_NAMES or any(
            marker in target.name.lower() for marker in ("auth", "security", "route", "api")
        ):
            warnings.append(f"high_impact_file_requires_manual_review:{relative}")

    if not any("/tests/" in f"/{path}" or path.endswith("/tests") for path in changed_paths):
        warnings.append("no_regression_test_file_changed")
    if any(Path(path).name.lower() in {"requirements.txt", "package.json", "pyproject.toml"} for path in changed_paths):
        warnings.append("dependency_change_requires_dependency_and_lockfile_review")

    ready = not blockers
    return {
        "ok": True,
        "repair_id": repair_id,
        "app_name": app_name,
        "status": "ready_for_human_review" if ready else "blocked",
        "ready_for_human_review": ready,
        "blockers": blockers,
        "warnings": sorted(set(warnings)),
        "checks": checks,
        "change_count": len(changes),
        "regression_test_file_changed": any("/tests/" in f"/{path}" for path in changed_paths),
        "writes_performed": False,
        "tests_executed": False,
        "proposal_applied": False,
        "human_review_required": True,
        "limitations": [
            "Static preflight only; no runtime tests or full UI/API compatibility proof.",
            "A clean report is not a security guarantee or proof that the repair is correct.",
        ],
    }
