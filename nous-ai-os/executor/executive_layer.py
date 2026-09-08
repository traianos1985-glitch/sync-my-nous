import time

from executor.autonomous_workspace import plan_from_prompt, create_workspace_mission, run_workspace_mission
from executor.mission_system import mission_status
from executor.agent_journal import write_journal
from executor.decision_memory import remember_system_decision


def executive_status():
    return {
        "time": time.time(),
        "mode": "executive_layer_v1",
        "flow": ["prompt", "plan", "mission", "safe_execution", "report"],
        "approval_required_for": ["deploy", "checkpoint", "tap", "swipe", "destructive_actions"],
        "missions": mission_status(),
    }


def executive_plan(prompt):
    plan = plan_from_prompt(prompt)
    return {
        "ok": True,
        "prompt": prompt,
        "plan": plan,
        "time": time.time(),
    }


def executive_run(prompt, max_steps=3, execute=True):
    plan = plan_from_prompt(prompt)
    created = create_workspace_mission(prompt)
    mission = created.get("mission", {})
    mission_id = mission.get("id")

    run_result = None
    if execute and mission_id:
        run_result = run_workspace_mission(mission_id, max_steps)

    report = {
        "ok": True,
        "prompt": prompt,
        "plan": plan,
        "mission_id": mission_id,
        "mission": mission,
        "executed": bool(execute),
        "run_result": run_result,
        "summary": {
            "created_mission": bool(mission_id),
            "safe_steps_requested": max_steps,
            "status": (run_result or {}).get("results", [{}])[-1].get("mission", {}).get("status") if run_result else mission.get("status"),
        },
        "time": time.time(),
    }

    write_journal("executive_run", report)
    remember_system_decision("executive_run", {
        "title": "Executive run: " + str(prompt)[:80],
        "reason": "NOUS planned and executed safe mission steps from user prompt.",
        "mission_id": mission_id,
        "action": "executive_run",
        "result": report.get("summary"),
        "confidence": 0.8,
        "tags": ["executive", "mission", "autonomy"],
    })
    return report
