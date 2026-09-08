import json
import os
import time

FILE = "data/executive_loop_v2.json"


def _load():
    if not os.path.exists(FILE):
        return {"runs": [], "last_run": None}
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return {"runs": [], "last_run": None, "error": "state_load_failed"}


def _save(state):
    os.makedirs("data", exist_ok=True)
    json.dump(state, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def run_executive_loop_v2(trigger="manual"):
    from executor.self_diagnosis import run_self_diagnosis
    from executor.code_analyst import analyze_latest_diagnosis
    from executor.autonomous_repair import propose_repair_from_diagnosis
    from executor.mission_planner import propose_mission_for_goal, mission_planner_status
    from executor.auto_mission_executor import run_auto_mission_executor
    from executor.goal_progress_intelligence import apply_goal_progress_intelligence
    from executor.executive_intelligence import executive_intelligence_status

    run = {
        "id": int(time.time_ns()),
        "time": time.time(),
        "trigger": trigger,
        "steps": {},
    }

    run["steps"]["diagnosis"] = run_self_diagnosis()
    run["steps"]["code_analysis"] = analyze_latest_diagnosis()

    if not run["steps"]["diagnosis"].get("ok"):
        run["steps"]["repair_proposal"] = propose_repair_from_diagnosis()
    else:
        run["steps"]["repair_proposal"] = {"ok": True, "skipped": True, "reason": "diagnosis_ok"}

    planner = mission_planner_status()
    if planner.get("pending", 0) == 0:
        run["steps"]["mission_proposal"] = propose_mission_for_goal()
    else:
        run["steps"]["mission_proposal"] = {"ok": True, "skipped": True, "reason": "pending_mission_proposal_exists"}

    run["steps"]["safe_execution"] = run_auto_mission_executor(
        max_missions=1,
        max_steps_per_mission=1,
        trigger="executive_loop_v2"
    )

    run["steps"]["goal_progress"] = apply_goal_progress_intelligence()
    run["steps"]["executive_intelligence"] = executive_intelligence_status()

    state = _load()
    state["last_run"] = run
    state.setdefault("runs", []).append(run)
    state["runs"] = state["runs"][-50:]
    _save(state)

    return {"ok": True, "run": run}


def executive_loop_v2_status():
    state = _load()
    return {
        "time": time.time(),
        "total_runs": len(state.get("runs", [])),
        "last_run": state.get("last_run"),
    }
