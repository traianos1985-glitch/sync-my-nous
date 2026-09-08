import os
import py_compile
from executor.git_agent import git_status
from executor.memory import save

FILES = [
    "executor/router.py",
    "executor/kernel.py",
    "executor/intent.py",
    "executor/tools.py",
    "executor/llm_core.py",
    "executor/brain.py",
    "executor/hybrid_agent.py",
    "executor/control_center.py",
]

def repair_check():
    results = {}

    for f in FILES:
        try:
            py_compile.compile(f, doraise=True)
            results[f] = "ok"
        except Exception as e:
            results[f] = str(e)

    status = git_status()

    out = {
        "compile": results,
        "git_status": status,
        "healthy": all(v == "ok" for v in results.values())
    }

    save({
        "event": "repair_check",
        "result": out
    })

    return out

def repair_advice():
    check = repair_check()

    if check["healthy"]:
        return {
            "status": "healthy",
            "message": "Ο ΝΟΥΣ φαίνεται σταθερός. Δεν χρειάζεται επισκευή.",
            "details": check
        }

    bad = {
        k: v for k, v in check["compile"].items()
        if v != "ok"
    }

    return {
        "status": "needs_repair",
        "broken_files": bad,
        "message": "Βρέθηκαν αρχεία με σφάλματα. Στείλε τα σφάλματα για στοχευμένη διόρθωση."
    }
