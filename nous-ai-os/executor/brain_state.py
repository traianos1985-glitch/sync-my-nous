import json
import os
import time

FILE = "data/brain_state.json"


def _safe_call(fn, fallback):
    try:
        return fn()
    except Exception as e:
        return {"error": str(e), "fallback": fallback}


def _load_json(path, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except Exception as e:
        return {"error": str(e), "path": path, "fallback": fallback}


def build_brain_state():
    from executor.goal_system import goal_status
    from executor.mission_system import mission_status, pending_approvals
    from executor.companion_bridge import companion_status
    from executor.vercel_deploy_integration import vercel_status
    from executor.reality_gate import reality_status
    from executor.ops_console import ops_status

    journal = _load_json("data/agent_journal.json", [])
    memory = _load_json("data/memory.json", {})
    goals = _safe_call(goal_status, {})
    missions = _safe_call(mission_status, {})
    approvals = _safe_call(pending_approvals, {})
    companion = _safe_call(companion_status, {})
    vercel = _safe_call(vercel_status, {})
    reality = _safe_call(reality_status, {})
    ops = _safe_call(ops_status, {})

    state = {
        "identity": {
            "name": "NOUS",
            "type": "personal_ai_operating_system",
            "owner_mode": True,
        },
        "time": time.time(),
        "goals": goals,
        "missions": missions,
        "approvals": approvals,
        "companion": companion,
        "deploy": {
            "vercel": vercel,
        },
        "reality": reality,
        "ops": ops,
        "memory_summary": {
            "type": type(memory).__name__,
            "size": len(memory) if hasattr(memory, "__len__") else None,
        },
        "journal_summary": {
            "events": len(journal) if isinstance(journal, list) else None,
            "recent": journal[-10:] if isinstance(journal, list) else journal,
        },
        "readiness": brain_readiness(goals, missions, approvals, companion, vercel, reality),
    }

    return state


def brain_readiness(goals, missions, approvals, companion, vercel, reality):
    ready = []
    missing = []

    if goals.get("total", 0) > 0:
        ready.append("goals")
    else:
        missing.append("goals")

    if missions.get("total", 0) >= 0:
        ready.append("missions")

    if companion.get("available"):
        ready.append("android_companion")
    else:
        missing.append("android_companion")

    if vercel.get("installed") and vercel.get("logged_in"):
        ready.append("vercel_deploy")
    else:
        missing.append("vercel_deploy")

    if reality.get("internet", {}).get("real") or reality.get("browser_read", {}).get("real"):
        ready.append("internet_or_browser_read")
    else:
        missing.append("internet_or_browser_read")

    approval_count = approvals.get("count", 0) if isinstance(approvals, dict) else 0

    return {
        "ready": ready,
        "missing": missing,
        "pending_approvals": approval_count,
        "cloud_ready_foundation": all(x in ready for x in ["goals", "missions", "vercel_deploy"]),
        "device_control_foundation": "android_companion" in ready,
    }


def save_brain_state():
    state = build_brain_state()
    os.makedirs("data", exist_ok=True)
    json.dump(state, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return state


def load_brain_state():
    return _load_json(FILE, {})


def brain_status():
    state = save_brain_state()
    return {
        "time": time.time(),
        "file": FILE,
        "identity": state.get("identity"),
        "readiness": state.get("readiness"),
        "goals": {
            "total": state.get("goals", {}).get("total"),
            "active": state.get("goals", {}).get("active"),
        },
        "missions": {
            "total": state.get("missions", {}).get("total"),
            "active": state.get("missions", {}).get("active"),
            "blocked": state.get("missions", {}).get("blocked"),
        },
        "approvals": state.get("approvals", {}),
    }
