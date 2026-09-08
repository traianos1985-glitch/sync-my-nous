import os
import time
from executor.app_builder import list_apps
from executor.agent_journal import write_journal
from executor.code_assistant import run_cmd

DEPLOY_FILE = "data/deployments.json"

def _load():
    import json
    if not os.path.exists(DEPLOY_FILE):
        return []
    try:
        return json.load(open(DEPLOY_FILE, "r", encoding="utf-8"))
    except Exception:
        return []

def _save(items):
    import json
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(DEPLOY_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def deploy_status():
    return {
        "mode": "local_static_apps",
        "apps": list_apps(),
        "deployments": _load(),
        "time": time.time(),
    }

def register_local_deploy(app_name):
    apps = list_apps()
    found = None
    for app in apps:
        if app.get("name") == app_name:
            found = app
            break

    if not found:
        return {"ok": False, "error": "app_not_found", "apps": apps}

    items = _load()
    item = {
        "id": int(time.time_ns()),
        "app": app_name,
        "url": found.get("url"),
        "path": found.get("path"),
        "status": "local_registered",
        "created": time.time(),
    }
    items.append(item)
    _save(items)
    write_journal("web_app_local_deploy_registered", item)
    return {"ok": True, "deployment": item}

def deploy_git_status():
    return run_cmd("git status --short")
