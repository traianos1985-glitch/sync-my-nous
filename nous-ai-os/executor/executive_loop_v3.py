import json, os, time

FILE = "data/executive_loop_v3.json"

def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return []

def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def run_executive_loop_v3(trigger="manual"):
    run = {"id": int(time.time_ns()), "time": time.time(), "trigger": trigger, "steps": {}}

    from executor.self_diagnosis import run_self_diagnosis
    from executor.deep_code_analyst import analyze_latest_diagnosis_deep
    from executor.self_healing_loop import run_self_healing_analysis
    from executor.mission_planner import propose_mission_for_goal
    from executor.auto_mission_executor import run_auto_mission_executor
    from executor.goal_progress_intelligence import apply_goal_progress_intelligence
    from executor.repository_graph import build_repository_graph
    from executor.knowledge_graph import build_knowledge_graph
    from executor.executive_memory_v3 import learn_from_recent_state
    from executor.pending_review import pending_review_status

    run["steps"]["observe_repository"] = build_repository_graph()
    run["steps"]["observe_knowledge"] = build_knowledge_graph()
    run["steps"]["diagnose"] = run_self_diagnosis()
    run["steps"]["analyze"] = analyze_latest_diagnosis_deep()

    if not run["steps"]["diagnose"].get("ok"):
        run["steps"]["self_healing"] = run_self_healing_analysis()
    else:
        run["steps"]["self_healing"] = {"ok": True, "skipped": True, "reason": "diagnosis_ok"}

    run["steps"]["plan_mission"] = propose_mission_for_goal()
    run["steps"]["safe_execute"] = run_auto_mission_executor(1, 1, "executive_loop_v3")
    run["steps"]["goal_progress"] = apply_goal_progress_intelligence()
    run["steps"]["learn"] = learn_from_recent_state()
    run["steps"]["pending"] = pending_review_status()

    items = _load()
    items.append(run)
    items = items[-50:]
    _save(items)

    return {"ok": True, "run": run}

def executive_loop_v3_status():
    items = _load()
    return {"time": time.time(), "total": len(items), "last_run": items[-1] if items else None}
