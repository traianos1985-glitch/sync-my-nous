import os
import subprocess
import time

from executor.memory import save

CONFIG = {
    "enabled": os.environ.get("NOUS_LOCAL_LLM", "0") == "1",
    "command": os.environ.get("NOUS_LOCAL_LLM_CMD", ""),
}


def local_llm_status():
    return {
        "enabled": CONFIG["enabled"],
        "command_configured": bool(CONFIG["command"]),
        "command": CONFIG["command"] if CONFIG["command"] else None,
        "time": time.time(),
    }


def ask_local(prompt, timeout=60):
    if not CONFIG["enabled"] or not CONFIG["command"]:
        return {
            "ok": False,
            "reason": "local_llm_not_configured",
            "status": local_llm_status(),
        }

    try:
        p = subprocess.run(
            CONFIG["command"],
            input=str(prompt),
            shell=True,
            text=True,
            capture_output=True,
            timeout=int(timeout),
        )

        result = {
            "ok": p.returncode == 0,
            "code": p.returncode,
            "response": p.stdout[-8000:],
            "error": p.stderr[-4000:],
        }

        save({"event": "local_llm_call", "ok": result["ok"]})
        return result

    except Exception as e:
        return {"ok": False, "error": str(e)}
