"""Safe preview/restore for NOUS runtime backups."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
import zipfile
from pathlib import PurePosixPath

RESTORE_DIR = "data/brain_restores"
ALLOWED_PREFIX = "data/"
BLOCKED = {
    "data/api_tokens.json",
    "data/secrets.json",
    "data/credentials.json",
}
BLOCKED_NAMES = {".env", ".env.local", ".env.production"}
BLOCKED_DIR_NAMES = {"brain_backups", "brain_restores", "__pycache__", ".cache"}
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
    """Return a canonical, permitted relative path below data/, otherwise None."""
    if not isinstance(value, str) or not value or "\\" in value or chr(0) in value:
        return None
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or candidate.as_posix() != value:
        return None
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    if not value.startswith(ALLOWED_PREFIX):
        return None
    if value in BLOCKED or any(part in BLOCKED_DIR_NAMES for part in parts):
        return None
    if parts[-1] in BLOCKED_NAMES:
        return None
    return value


def _inside_data_dir(relative_path: str) -> str | None:
    data_root = os.path.abspath("data")
    target = os.path.abspath(os.path.join(data_root, relative_path.removeprefix("data/")))
    try:
        if os.path.commonpath([data_root, target]) != data_root:
            return None
    except ValueError:
        return None
    return target


def _has_symlink_component(relative_path: str) -> bool:
    """Reject symlinked data roots, parent directories, and final targets."""
    current = os.path.abspath("data")
    if os.path.islink(current):
        return True
    for part in relative_path.removeprefix("data/").split("/"):
        current = os.path.join(current, part)
        if os.path.islink(current):
            return True
    return False


def inspect_brain_backup(path):
    if not path or not os.path.isfile(path) or os.path.islink(path):
        return {"ok": False, "error": "backup_not_found", "path": path}
    if os.path.getsize(path) > MAX_BACKUP_BYTES:
        return {"ok": False, "error": "backup_too_large", "path": path}
    if not zipfile.is_zipfile(path):
        return {"ok": False, "error": "not_a_zip_file", "path": path}

    try:
        with zipfile.ZipFile(path, "r") as archive:
            names = archive.namelist()
            if names.count("manifest.json") != 1:
                return {"ok": False, "error": "manifest_missing_or_duplicate", "path": path}
            if len(names) != len(set(names)):
                return {"ok": False, "error": "duplicate_zip_entries", "path": path}

            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            if (not isinstance(manifest, dict)
                    or manifest.get("type") != "NOUS_BRAIN_BACKUP"
                    or not isinstance(manifest.get("files"), list)):
                return {"ok": False, "error": "invalid_manifest", "path": path}

            files = []
            problems = []
            seen = set()
            total_size = 0
            manifest_paths = set()
            for item in manifest["files"]:
                if not isinstance(item, dict):
                    problems.append({"error": "invalid_manifest_entry"})
                    continue
                raw_path = item.get("path")
                file_path = _safe_backup_path(raw_path)
                expected = item.get("sha256")
                if file_path is None:
                    problems.append({"path": raw_path, "error": "path_not_allowed"})
                    continue
                if file_path in seen:
                    problems.append({"path": file_path, "error": "duplicate_manifest_path"})
                    continue
                seen.add(file_path)
                manifest_paths.add(file_path)
                if file_path not in names:
                    problems.append({"path": file_path, "error": "missing_from_zip"})
                    continue
                info = archive.getinfo(file_path)
                if info.file_size > MAX_FILE_BYTES:
                    problems.append({"path": file_path, "error": "file_too_large"})
                    continue
                total_size += info.file_size
                if total_size > MAX_BACKUP_BYTES:
                    problems.append({"error": "expanded_backup_too_large"})
                    break
                data = archive.read(file_path)
                if file_path.endswith(".json"):
                    try:
                        json.loads(data.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        problems.append({"path": file_path, "error": "invalid_json"})
                        continue
                actual = _sha256_bytes(data)
                files.append({
                    "path": file_path,
                    "size": len(data),
                    "sha256": actual,
                    "expected_sha256": expected,
                    "sha256_ok": isinstance(expected, str) and actual == expected,
                })
                if not isinstance(expected, str) or actual != expected:
                    problems.append({"path": file_path, "error": "sha256_mismatch"})
                expected_size = item.get("size")
                if expected_size is not None and (
                    isinstance(expected_size, bool) or expected_size != len(data)
                ):
                    problems.append({"path": file_path, "error": "size_mismatch"})

            unexpected = set(names) - manifest_paths - {"manifest.json"}
            if unexpected:
                problems.append({"error": "unlisted_zip_entries", "entries": sorted(unexpected)[:20]})
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


def _fsync_directory(directory):
    try:
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def _atomic_write(path, data):
    directory = os.path.dirname(path) or "."
    fd, temp_path = tempfile.mkstemp(prefix=".nous-restore-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp_path, path)
        _fsync_directory(directory)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


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

    # Read and validate every payload before touching the live runtime state.
    payloads = []
    try:
        with zipfile.ZipFile(path, "r") as archive:
            for item in inspection["files"]:
                relative = item["path"]
                target = _inside_data_dir(relative)
                if target is None or _has_symlink_component(relative):
                    return {"ok": False, "error": "restore_target_not_allowed", "path": relative}
                data = archive.read(relative)
                if _sha256_bytes(data) != item["sha256"]:
                    return {"ok": False, "error": "backup_changed_during_restore", "path": relative}
                if relative.endswith(".json"):
                    json.loads(data.decode("utf-8"))
                payloads.append((relative, target, data))
    except Exception as exc:
        return {"ok": False, "error": "restore_preflight_failed", "details": str(exc)}

    stamp = time.time_ns()
    safety_dir = os.path.join(RESTORE_DIR, f"before_restore_{stamp}")
    staged = []
    changed = []
    originals = {}
    try:
        os.makedirs(safety_dir, exist_ok=False)
        # Prepare directories, reject symlinks after creation, and stage all new
        # files before replacing any live file.
        for relative, target, data in payloads:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if _has_symlink_component(relative):
                raise RuntimeError(f"restore_target_not_allowed:{relative}")
            if os.path.exists(target):
                if not os.path.isfile(target):
                    raise RuntimeError(f"restore_target_not_regular_file:{relative}")
                safe_copy = os.path.join(safety_dir, relative)
                os.makedirs(os.path.dirname(safe_copy), exist_ok=True)
                shutil.copy2(target, safe_copy)
                with open(safe_copy, "rb") as saved:
                    originals[target] = saved.read()
            else:
                originals[target] = None
            fd, temp_path = tempfile.mkstemp(
                prefix=".nous-restore-", suffix=".tmp", dir=os.path.dirname(target)
            )
            with os.fdopen(fd, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            staged.append((relative, target, temp_path))

        for relative, target, temp_path in staged:
            if _has_symlink_component(relative):
                raise RuntimeError(f"restore_target_not_allowed:{relative}")
            os.replace(temp_path, target)
            changed.append(target)
            _fsync_directory(os.path.dirname(target))
        return {
            "ok": True,
            "restored": [relative for relative, _, _ in staged],
            "safety_backup": safety_dir,
            "time": time.time(),
            "atomic_per_file": True,
        }
    except Exception as exc:
        rollback_errors = []
        for target in reversed(changed):
            try:
                original = originals.get(target)
                if original is None:
                    if os.path.exists(target):
                        os.unlink(target)
                else:
                    _atomic_write(target, original)
            except Exception as rollback_exc:
                rollback_errors.append({"path": target, "error": str(rollback_exc)})
        return {
            "ok": False,
            "error": "restore_failed",
            "details": str(exc),
            "rolled_back": not rollback_errors,
            "rollback_errors": rollback_errors,
            "safety_backup": safety_dir,
        }
    finally:
        for _, _, temp_path in staged:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except OSError:
                pass


def restore_status():
    os.makedirs(RESTORE_DIR, exist_ok=True)
    return {
        "time": time.time(),
        "restore_dir": RESTORE_DIR,
        "allowed_prefix": ALLOWED_PREFIX,
        "blocked": sorted(BLOCKED),
        "safety_backups": sorted(os.listdir(RESTORE_DIR), reverse=True),
    }
