import json
import os
import time

REPORT_FILE = "data/code_analysis_reports.json"


def _load():
    if not os.path.exists(REPORT_FILE):
        return []
    try:
        return json.load(open(REPORT_FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(REPORT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


RULES = [
    ("401", "auth/security failure", ["executor/security.py", "executor/router.py", "executor/nous_ui.py"]),
    ("unauthorized", "auth/security failure", ["executor/security.py", "executor/router.py", "executor/nous_ui.py"]),
    ("404", "missing route", ["executor/router.py", "executor/nous_ui.py"]),
    ("endpoint_failed", "backend route failure", ["executor/router.py"]),
    ("compile_error", "python compile error", []),
    ("dashboard", "frontend/dashboard issue", ["executor/nous_ui.py", "executor/router.py"]),
    ("button", "frontend action issue", ["executor/nous_ui.py"]),
    ("mission", "mission system issue", ["executor/mission_system.py", "executor/mission_planner.py"]),
    ("goal", "goal/progress issue", ["executor/goal_system.py", "executor/goal_progress_intelligence.py"]),
    ("repair", "repair system issue", ["executor/autonomous_repair.py", "executor/self_diagnosis.py"]),
    ("scheduler", "scheduler issue", ["executor/executive_scheduler_loop.py", "executor/auto_mission_executor.py"]),
]


def analyze_problem(problem):
    text = json.dumps(problem, ensure_ascii=False).lower()
    matches = []

    for key, cause, files in RULES:
        if key in text:
            matches.append({
                "rule": key,
                "root_cause": cause,
                "candidate_files": files,
                "confidence": 0.75,
            })

    if not matches:
        matches.append({
            "rule": "fallback",
            "root_cause": "unknown/general issue",
            "candidate_files": ["executor/router.py", "executor/nous_ui.py"],
            "confidence": 0.35,
        })

    files = []
    for m in matches:
        for f in m["candidate_files"]:
            if f not in files:
                files.append(f)

    report = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "problem": problem,
        "root_cause": matches[0]["root_cause"],
        "confidence": max([m["confidence"] for m in matches]),
        "matches": matches,
        "candidate_files": files,
        "suggested_next_step": "Generate repair proposal, inspect candidate files, then require user approval before patching.",
    }

    items = _load()
    items.append(report)
    _save(items)

    return {"ok": True, "report": report}


def analyze_latest_diagnosis():
    try:
        from executor.self_diagnosis import self_diagnosis_status
        status = self_diagnosis_status()
        problem = status.get("report", status)
    except Exception as e:
        problem = {"error": str(e)}

    return analyze_problem(problem)


def list_code_analysis_reports(limit=20):
    return _load()[-int(limit):]


def code_analyst_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "recent": items[-10:],
    }


def generate_patch_suggestion(problem):
    analysis = analyze_problem(problem)["report"]

    suggestion = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "analysis_id": analysis["id"],
        "status": "suggested",
        "root_cause": analysis["root_cause"],
        "candidate_files": analysis["candidate_files"],
        "patch_type": "manual_review_required",
        "risk": "low" if analysis["confidence"] >= 0.7 else "medium",
        "description": "Suggested repair requires inspection before applying. No automatic file changes were made.",
        "diff": "",
        "next_actions": [
            "Open candidate files",
            "Inspect related routes/functions",
            "Create concrete patch",
            "Run py_compile",
            "Run dashboard action audit",
            "Require user approval",
        ],
    }

    return {"ok": True, "analysis": analysis, "suggestion": suggestion}
