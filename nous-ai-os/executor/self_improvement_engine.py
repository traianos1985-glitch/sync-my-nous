import json
import os
import shutil
import time
from pathlib import Path

from executor.code_assistant import code_health
from executor.guardian_policy import check_action
from executor.agent_journal import write_journal
from executor.memory import save

PATCH_DIR = "data/patches"
BACKUP_DIR = "data/patch_backups"

ALLOWED_FILES = {
    "executor/agent_review.py",
    "executor/curiosity_agent.py",
    "executor/learning_engine.py",
    "executor/decision_engine.py",
    "executor/master_agent.py",
    "executor/guardian_policy.py",
    "executor/real_research_engine.py",
    "executor/app_evolver.py",
    "executor/android_control.py",
}


def _ensure_dirs():
    os.makedirs(PATCH_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)


def allowed_file(path):
    return str(path) in ALLOWED_FILES


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
        "reason": reason,
        "status": "pending",
        "created": time.time(),
        "applied": None,
        "error": None,
    }

    path = f"{PATCH_DIR}/{patch['id']}.json"
    json.dump(patch, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    write_journal("patch_request_created", {"patch": path, "file": file_path})
    return {"created": True, "patch": patch, "path": path}


def list_patches():
    _ensure_dirs()
    items = []

    for path in sorted(Path(PATCH_DIR).glob("*.json")):
        try:
            items.append(json.load(open(path, "r", encoding="utf-8")))
        except Exception:
            pass

    return items


def _compile_file(file_path):
    import subprocess
    p = subprocess.run(
        f"python -m py_compile {file_path}",
        shell=True,
        text=True,
        capture_output=True,
        timeout=30,
    )
    return {
        "ok": p.returncode == 0,
        "code": p.returncode,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    }


def apply_patch(patch_id):
    _ensure_dirs()

    policy = check_action("modify_core_without_test")
    if policy.get("allowed"):
        return {"ok": False, "error": "policy_misconfigured"}

    path = Path(PATCH_DIR) / f"{patch_id}.json"
    if not path.exists():
        return {"ok": False, "error": "patch_not_found", "id": patch_id}

    patch = json.load(open(path, "r", encoding="utf-8"))
    file_path = patch.get("file")

    if not allowed_file(file_path):
        patch["status"] = "blocked"
        patch["error"] = "file_not_allowed"
        json.dump(patch, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return {"ok": False, "error": "file_not_allowed"}

    target = Path(file_path)
    if not target.exists():
        patch["status"] = "failed"
        patch["error"] = "target_not_found"
        json.dump(patch, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return {"ok": False, "error": "target_not_found"}

    backup = Path(BACKUP_DIR) / f"{patch_id}_{target.name}.bak"
    shutil.copyfile(target, backup)

    original = target.read_text(encoding="utf-8")

    try:
        target.write_text(patch.get("new_content", ""), encoding="utf-8")
        compile_result = _compile_file(file_path)

        if not compile_result.get("ok"):
            target.write_text(original, encoding="utf-8")
            patch["status"] = "rolled_back"
            patch["error"] = compile_result
            json.dump(patch, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            write_journal("patch_rolled_back", {"patch_id": patch_id, "file": file_path})
            return {
                "ok": False,
                "rolled_back": True,
                "compile": compile_result,
                "backup": str(backup),
            }

        patch["status"] = "applied"
        patch["applied"] = time.time()
        patch["error"] = None
        json.dump(patch, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

        result = {
            "ok": True,
            "file": file_path,
            "backup": str(backup),
            "compile": compile_result,
            "health": code_health(),
        }

        write_journal("patch_applied", result)
        save({"event": "self_improvement_patch_applied", "result": result})
        return result

    except Exception as e:
        target.write_text(original, encoding="utf-8")
        patch["status"] = "rolled_back"
        patch["error"] = str(e)
        json.dump(patch, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return {"ok": False, "rolled_back": True, "error": str(e), "backup": str(backup)}


def self_improvement_status():
    return {
        "allowed_files": sorted(ALLOWED_FILES),
        "patches": list_patches(),
        "health": code_health(),
        "time": time.time(),
    }
