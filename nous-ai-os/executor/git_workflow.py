import time
from executor.code_assistant import run_cmd, code_health
from executor.agent_journal import write_journal

def git_workflow_status():
    return {
        "time": time.time(),
        "git": run_cmd("git status --short"),
        "health": code_health(),
    }

def git_safe_checkpoint(message="NOUS checkpoint"):
    health = code_health()
    broken = [k for k, v in health.get("compile", {}).items() if not v.get("ok")]
    if broken:
        return {"ok": False, "error": "compile_failed", "broken": broken}

    add = run_cmd("git add .")
    commit = run_cmd(f'git commit -m "{message}"')
    push = run_cmd("git push")

    result = {
        "ok": bool(push.get("ok")),
        "add": add,
        "commit": commit,
        "push": push,
        "time": time.time(),
    }
    write_journal("git_safe_checkpoint", result)
    return result
