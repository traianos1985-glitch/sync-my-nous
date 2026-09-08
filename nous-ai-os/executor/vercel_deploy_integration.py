import json
import os
import re
import time

from executor.code_assistant import run_cmd
from executor.agent_journal import write_journal

FILE = "data/vercel_deployments.json"


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _extract_urls(text):
    return re.findall(r"https://[^\s]+", text or "")


def vercel_status():
    version = run_cmd("vercel --version")
    whoami = run_cmd("vercel whoami")
    return {
        "installed": bool(version.get("ok")),
        "logged_in": bool(whoami.get("ok")),
        "version": version,
        "whoami": whoami,
        "deployments": _load()[-20:],
        "time": time.time(),
    }


def vercel_deploy(path, prod=True):
    if not path:
        return {"ok": False, "error": "missing_path"}

    if not os.path.exists(path):
        return {"ok": False, "error": "path_not_found", "path": path}

    cmd = "vercel --prod --yes" if prod else "vercel --yes"
    result = run_cmd(f"cd {path} && {cmd}")

    urls = _extract_urls((result.get("stdout", "") or "") + "\n" + (result.get("stderr", "") or ""))

    item = {
        "id": int(time.time_ns()),
        "path": path,
        "prod": prod,
        "ok": bool(result.get("ok")),
        "urls": urls,
        "created": time.time(),
        "result": result,
    }

    items = _load()
    items.append(item)
    _save(items)

    write_journal("vercel_deploy_run", item)

    return item
