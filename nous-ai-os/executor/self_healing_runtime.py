import time

from executor.compile_check import check as compile_check
from executor.repair_agent import repair_check
from executor.memory import save

STATE = "data/self_healing_status.json"


def health_snapshot():
    repair = repair_check()
    return {
        "time": time.time(),
        "repair": repair,
        "healthy": bool(repair.get("healthy")) if isinstance(repair, dict) else False,
    }


def self_heal_check():
    snapshot = health_snapshot()

    result = {
        "checked": True,
        "healthy": snapshot.get("healthy"),
        "action": "none",
        "snapshot": snapshot,
    }

    if not snapshot.get("healthy"):
        result["action"] = "diagnose_only"
        result["note"] = "Το σύστημα δεν είναι healthy. Δεν έγινε αυτόματη διόρθωση χωρίς έγκριση."

    save({"event": "self_heal_check", "result": result})
    return result
