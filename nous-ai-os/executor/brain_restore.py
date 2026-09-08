import json
import os
import time
import hashlib
import zipfile
import shutil

RESTORE_DIR = "data/brain_restores"
ALLOWED_PREFIX = "data/"
BLOCKED = {
    "data/api_tokens.json",
}


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def inspect_brain_backup(path):
    if not path or not os.path.exists(path):
        return {"ok": False, "error": "backup_not_found", "path": path}

    if not zipfile.is_zipfile(path):
        return {"ok": False, "error": "not_a_zip_file", "path": path}

    with zipfile.ZipFile(path, "r") as z:
        names = z.namelist()

        if "manifest.json" not in names:
            return {"ok": False, "error": "manifest_missing", "path": path}

        manifest = json.loads(z.read("manifest.json").decode("utf-8"))

        files = []
        problems = []

        for item in manifest.get("files", []):
            fpath = item.get("path")
            expected = item.get("sha256")

            if not fpath or fpath not in names:
                problems.append({"path": fpath, "error": "missing_from_zip"})
                continue

            if not fpath.startswith(ALLOWED_PREFIX):
                problems.append({"path": fpath, "error": "path_not_allowed"})
                continue

            if fpath in BLOCKED:
                problems.append({"path": fpath, "error": "blocked_file"})
                continue

            data = z.read(fpath)
            actual = _sha256_bytes(data)

            files.append({
                "path": fpath,
                "size": len(data),
                "sha256": actual,
                "expected_sha256": expected,
                "sha256_ok": actual == expected,
            })

            if actual != expected:
                problems.append({"path": fpath, "error": "sha256_mismatch"})

        return {
            "ok": len(problems) == 0,
            "path": path,
            "backup_sha256": _sha256_file(path),
            "manifest": manifest,
            "files": files,
            "problems": problems,
            "time": time.time(),
        }


def restore_brain_backup(path, apply=False):
    inspection = inspect_brain_backup(path)
    if not inspection.get("ok"):
        return {
            "ok": False,
            "error": "inspection_failed",
            "inspection": inspection,
        }

    if not apply:
        return {
            "ok": True,
            "preview": True,
            "message": "Backup verified. Set apply=true to restore files.",
            "inspection": inspection,
        }

    os.makedirs(RESTORE_DIR, exist_ok=True)
    stamp = int(time.time())
    safety_dir = f"{RESTORE_DIR}/before_restore_{stamp}"
    os.makedirs(safety_dir, exist_ok=True)

    restored = []

    with zipfile.ZipFile(path, "r") as z:
        for f in inspection.get("files", []):
            target = f["path"]

            if os.path.exists(target):
                os.makedirs(os.path.dirname(f"{safety_dir}/{target}"), exist_ok=True)
                shutil.copy2(target, f"{safety_dir}/{target}")

            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as out:
                out.write(z.read(target))

            restored.append(target)

    return {
        "ok": True,
        "restored": restored,
        "safety_backup": safety_dir,
        "time": time.time(),
    }


def restore_status():
    os.makedirs(RESTORE_DIR, exist_ok=True)
    return {
        "time": time.time(),
        "restore_dir": RESTORE_DIR,
        "allowed_prefix": ALLOWED_PREFIX,
        "blocked": sorted(BLOCKED),
        "safety_backups": sorted(os.listdir(RESTORE_DIR), reverse=True),
    }
