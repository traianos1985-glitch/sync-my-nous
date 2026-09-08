import os
import time
import shutil

FILES = [
    "executor/router.py",
    "executor/kernel.py",
    "executor/intent.py",
    "executor/llm_core.py",
    "executor/brain.py",
    "executor/hybrid_agent.py",
    "executor/control_center.py",
]

def status():
    return {
        "files_ok": [f for f in FILES if os.path.exists(f)],
        "system": "healthy"
    }

def backup():
    ts = int(time.time())
    dst = f"backups/nous_backup_{ts}"
    os.makedirs(dst, exist_ok=True)
    for f in FILES:
        if os.path.exists(f):
            shutil.copy(f, dst + "/" + os.path.basename(f))
    return {"backup": dst, "status": "created"}
