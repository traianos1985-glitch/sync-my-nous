import os
import shlex
import subprocess
import time

from executor.memory import save

SAFE_MODULES = [
    "executor/router.py",
    "executor/intent.py",
    "executor/tools.py",
    "executor/scheduler_agent.py",
    "executor/autonomous_loop.py",
    "executor/autonomy_service.py",
    "executor/task_queue.py",
    "executor/goal_executor.py",
    "executor/project_progress.py",
    "executor/runtime_metrics.py",
    "executor/curiosity_agent.py",
    "executor/learning_engine.py",
]


def run_cmd(cmd, cwd=None, timeout=30):
    """Run a bounded argv command without shell interpretation."""
    try:
        argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
        if not argv or any(not isinstance(arg, str) for arg in argv):
            return {"ok": False, "error": "invalid_command"}
        p = subprocess.run(
            argv,
            cwd=cwd,
            shell=False,
            text=True,
            capture_output=True,
            timeout=max(1, min(int(timeout), 300)),
        )
        return {
            "ok": p.returncode == 0,
            "code": p.returncode,
            "stdout": p.stdout[-4000:],
            "stderr": p.stderr[-4000:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "command_timeout"}
    except (OSError, TypeError, ValueError, OverflowError):
        return {"ok": False, "error": "command_execution_failed"}


def code_health():
    results = {}

    for path in SAFE_MODULES:
        if os.path.exists(path):
            results[path] = run_cmd(["python", "-m", "py_compile", path])

    try:
        git = run_cmd(["git", "--no-optional-locks", "status", "--short"])
    except Exception as e:
        git = {"ok": False, "error": str(e)}

    output = {
        "time": time.time(),
        "compile": results,
        "git": git,
    }

    save({"event": "code_health", "ok": all(x.get("ok") for x in results.values())})
    return output


def code_advice():
    health = code_health()
    broken = [k for k, v in health["compile"].items() if not v.get("ok")]

    if broken:
        advice = [
            "Υπάρχουν compile errors.",
            "Σταμάτα τις νέες αλλαγές.",
            "Διόρθωσε πρώτα τα modules που αποτυγχάνουν.",
            "Μετά κάνε py_compile και git checkpoint."
        ]
    else:
        advice = [
            "Ο βασικός κώδικας κάνει compile.",
            "Συνέχισε με μικρά patches.",
            "Μετά από κάθε πακέτο κάνε commit και push.",
        ]

    return {
        "health": health,
        "advice": advice,
    }
