import os, shutil

def quarantine(name):
    src = f"executor/plugins/{name}.py"
    if not os.path.exists(src):
        return {"success": False, "error": "plugin_not_found"}
    os.makedirs("executor/quarantine", exist_ok=True)
    dst = f"executor/quarantine/{name}.py"
    shutil.move(src, dst)
    return {"success": True, "quarantined": name, "path": dst}
