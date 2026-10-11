import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from executor.code_assistant import code_health
from executor.guardian_policy import check_action
from executor.agent_journal import write_journal
from executor.memory import save

PATCH_DIR = "data/patches"
BACKUP_DIR = "data/patch_backups"

# Security policy and control-plane modules must only change through reviewed source PRs.
ALLOWED_FILES = {
    "executor/agent_review.py",
    "executor/curiosity_agent.py",
    "executor/learning_engine.py",
    "executor/decision_engine.py",
    "executor/master_agent.py",
    "executor/real_research_engine.py",
    "executor/app_evolver.py",
}


def _ensure_dirs():
    os.makedirs(PATCH_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)


def allowed_file(path):
    return isinstance(path, str) and path in ALLOWED_FILES


def _valid_patch_id(patch_id):
    return bool(re.fullmatch(r"[0-9]{1,20}", str(patch_id or "")))


def create_patch_request(file_path, new_content, reason="manual"):
    _ensure_dirs()
    file_path = str(file_path)
    if not allowed_file(file_path):
        return {
            "created": False,
            "error": "file_not_allowed",
            "file": file_path,
            "allowed_files": sorted(ALLOWED_FILES),
        }

    patch = {
        "id": int(time.time_ns()),
        "file": file_path,
        "new_content": str(new_content),
        "reason": str(reason)[:1000],
        "status": "pending",
        "created": time.time(),
        "applied": None,
        "error": None,
    }
    path = Path(PATCH_DIR) / f"{patch['id']}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(patch, handle, ensure_ascii=False, indent=2)
    write_journal("patch_request_created", {"patch": str(path), "file": file_path})
    return {"created": True, "patch": patch, "path": str(path)}


def list_patches():
    _ensure_dirs()
    items = []
    for path in sorted(Path(PATCH_DIR).glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                items.append(json.load(handle))
        except (OSError, ValueError, TypeError):
            continue
    return items


def _compile_file(file_path):
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(file_path)],
        shell=False,
        text=True,
        capture_output=True,
        timeout=30,
    )
    return {
        "ok": result.returncode == 0,
        "code": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


def apply_patch(patch_id):
    if not _valid_patch_id(patch_id):
        return {"ok": False, "error": "invalid_patch_id"}
    _ensure_dirs()
    policy = check_action("modify_core_without_test")
    if policy.get("allowed"):
        return {"ok": False, "error": "policy_misconfigured"}

    patch_path = Path(PATCH_DIR) / f"{patch_id}.json"
    if not patch_path.is_file():
        return {"ok": False, "error": "patch_not_found", "id": str(patch_id)}
    try:
        with patch_path.open("r", encoding="utf-8") as handle:
            patch = json.load(handle)
    except (OSError, ValueError):
        return {"ok": False, "error": "invalid_patch"}
    file_path = patch.get("file")
    if not allowed_file(file_path):
        patch["status"] = "blocked"
        patch["error"] = "file_not_allowed"
        with patch_path.open("w", encoding="utf-8") as handle:
            json.dump(patch, handle, ensure_ascii=False, indent=2)
        return {"ok": False, "error": "file_not_allowed"}

    target = Path(file_path)
    if not target.is_file() or target.is_symlink():
        return {"ok": False, "error": "target_not_regular_file"}
    backup = Path(BACKUP_DIR) / f"{patch_id}_{target.name}.bak"
    temporary_path = None
    try:
        shutil.copyfile(target, backup)
        target.parent.mkdir(parents=True, exist_ok=True)
        original = target.read_bytes()
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.",
            suffix=".tmp.py", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(str(patch.get("new_content", "")).encode("utf-8"))
            temporary.flush()
            os.fsync(temporary.fileno())

        compile_result = _compile_file(temporary_path)
        if not compile_result.get("ok"):
            patch["status"] = "rolled_back"
            patch["error"] = compile_result
            with patch_path.open("w", encoding="utf-8") as handle:
                json.dump(patch, handle, ensure_ascii=False, indent=2)
            return {"ok": False, "rolled_back": True, "compile": compile_result, "backup": str(backup)}

        os.replace(temporary_path, target)
        temporary_path = None
        patch["status"] = "applied"
        patch["applied"] = time.time()
        patch["error"] = None
        with patch_path.open("w", encoding="utf-8") as handle:
            json.dump(patch, handle, ensure_ascii=False, indent=2)

        result = {
            "ok": True, "file": file_path, "backup": str(backup),
            "compile": compile_result, "health": code_health(),
        }
        write_journal("patch_applied", result)
        save({"event": "self_improvement_patch_applied", "result": result})
        return result
    except Exception:
        # The original source is never opened for writing before atomic replacement.
        return {"ok": False, "error": "patch_application_failed", "backup": str(backup)}
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def self_improvement_status():
    return {
        "allowed_files": sorted(ALLOWED_FILES),
        "patches": list_patches(),
        "health": code_health(),
        "time": time.time(),
    }
