"""Safe preview/restore for NOUS brain backups."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import zipfile
from pathlib import PurePosixPath

RESTORE_DIR = "data/brain_restores"
ALLOWED_PREFIX = "data/"
BLOCKED = {"data/api_tokens.json"}
BLOCKED_DIRS = {"data/brain_backups", "data/brain_restores"}
MAX_BACKUP_BYTES = 256 * 1024 * 1024
MAX_FILE_BYTES = 64 * 1024 * 1024


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_backup_path(value: object) -> str | None:
    """Return a canonical, permitted relative JSON path, otherwise None."""
    if not isinstance(value, str) or not value or "\\" in value or chr(0) in value:
        return None
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or candidate.as_posix() != value:
        return None
    if any(part in {"", ".", ".."} for part in value.split("/")):
        return None
    if not value.startswith(ALLOWED_PREFIX) or not value.endswith(".json"):
        return None
    if value in BLOCKED:
        return None
    if any(value == d or value.startswith(d + "/") for d in BLOCKED_DIRS):
        return None
    return value


def _inside_data_dir(relative_path: str) -> str | None:
    data_root = os.path.realpath("data")
    target = os.path.realpath(os.path.join(data_root, relative_path.removeprefix("data/")))
    try:
        if os.path.commonpath([data_root, target]) != data_root:
            return None
    except ValueError:
        return None
    return target


def inspect_brain_backup(path):
    if not path or not os.path.isfile(path):
        return {"ok": False, "error": "backup_not_found", "path": path}
    if os.path.getsize(path) > MAX_BACKUP_BYTES:
        return {"ok": False, "error": "backup_too_large", "path": path}
    if not zipfile.is_zipfile(path):
        return {"ok": False, "error": "not_a_zip_file", "path": path}

    try:
        with zipfile.ZipFile(path, "r") as z:
            names = z.namelist()
            if names.count("manifest.json") != 1:
                return {"ok": False, "error": "manifest_missing_or_duplicate", "path": path}
            if len(names) != len(set(names)):
                return {"ok": False, "error": "duplicate_zip_entries", "path": path}

            manifest = json.loads(z.read("manifest.json").decode("utf-8"))
            if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
                return {"ok": False, "error": "invalid_manifest", "path": path}

            files = []
            problems = []
            seen = set()
            total_size = 0
            for item in manifest["files"]:
                if not isinstance(item, dict):
                    problems.append({"error": "invalid_manifest_entry"})
                    continue
                raw_path = item.get("path")
                fpath = _safe_backup_path(raw_path)
                expected = item.get("sha256")
                if fpath is None:
                    problems.append({"path": raw_path, "error": "path_not_allowed"})
                    continue
                if fpath in seen:
                    problems.append({"path": fpath, "error": "duplicate_manifest_path"})
                    continue
                seen.add(fpath)
                if fpath not in names:
                    problems.append({"path": fpath, "error": "missing_from_zip"})
                    continue
                info = z.getinfo(fpath)
                if info.file_size > MAX_FILE_BYTES:
                    problems.append({"path": fpath, "error": "file_too_large"})
                    continue
                total_size += info.file_size
                if total_size > MAX_BACKUP_BYTES:
                    problems.append({"error": "expanded_backup_too_large"})
                    break
                data = z.read(fpath)
                try:
                    json.loads(data.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    problems.append({"path": fpath, "error": "invalid_json"})
                    continue
                actual = _sha256_bytes(data)
                files.append({
                    "path": fpath,
                    "size": len(data),
                    "sha256": actual,
                    "expected_sha256": expected,
                    "sha256_ok": isinstance(expected, str) and actual == expected,
                })
                if not isinstance(expected, str) or actual != expected:
                    problems.append({"path": fpath, "error": "sha256_mismatch"})

            if not files:
                problems.append({"error": "no_restorable_files"})
            return {
                "ok": len(problems) == 0,
                "path": path,
                "backup_sha256": _sha256_file(path),
                "manifest": manifest,
                "files": files,
                "problems": problems,
                "time": time.time(),
            }
    except (OSError, zipfile.BadZipFile, RuntimeError, UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
        return {"ok": False, "error": "backup_read_failed", "details": str(exc), "path": path}


def restore_brain_backup(path, apply=False):
    inspection = inspect_brain_backup(path)
    if not inspection.get("ok"):
        return {"ok": False, "error": "inspection_failed", "inspection": inspection}
    if not apply:
        return {
            "ok": True,
            "preview": True,
            "message": "Backup verified. Set apply=true to restore files.",
            "inspection": inspection,
        }

    os.makedirs(RESTORE_DIR, exist_ok=True)
    stamp = int(time.time())
    safety_dir = os.path.join(RESTORE_DIR, f"before_restore_{stamp}")
    os.makedirs(safety_dir, exist_ok=True)
    restored = []

    with zipfile.ZipFile(path, "r") as z:
        for item in inspection["files"]:
            relative = item["path"]
            target = _inside_data_dir(relative)
            if target is None:
                return {"ok": False, "error": "restore_target_not_allowed", "path": relative}
            os.makedirs(os.path.dirname(target), exist_ok=True)
            target = _inside_data_dir(relative)
            if target is None:
                return {"ok": False, "error": "restore_target_not_allowed", "path": relative}
            if os.path.exists(target):
                safe_copy = os.path.join(safety_dir, relative)
                os.makedirs(os.path.dirname(safe_copy), exist_ok=True)
                shutil.copy2(target, safe_copy)
            data = z.read(relative)
            # Revalidate content immediately before writing.
            json.loads(data.decode("utf-8"))
            with open(target, "wb") as out:
                out.write(data)
            restored.append(relative)

    return {"ok": True, "restored": restored, "safety_backup": safety_dir, "time": time.time()}


def restore_status():
    os.makedirs(RESTORE_DIR, exist_ok=True)
    return {
        "time": time.time(),
        "restore_dir": RESTORE_DIR,
        "allowed_prefix": ALLOWED_PREFIX,
        "blocked": sorted(BLOCKED),
        "safety_backups": sorted(os.listdir(RESTORE_DIR), reverse=True),
    }
