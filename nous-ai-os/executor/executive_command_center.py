import time


def executive_command_center_status():
    data = {"time": time.time(), "ok": True}

    try:
        from executor.pending_review import pending_review_status
        data["pending"] = pending_review_status()
    except Exception as e:
        data["pending_error"] = str(e)

    try:
        from executor.goal_system import goal_status
        data["goals"] = goal_status()
    except Exception as e:
        data["goals_error"] = str(e)

    try:
        from executor.mission_system import mission_status
        data["missions"] = mission_status()
    except Exception as e:
        data["missions_error"] = str(e)

    try:
        from executor.executive_intelligence import executive_intelligence_status
        data["intelligence"] = executive_intelligence_status()
    except Exception as e:
        data["intelligence_error"] = str(e)

    try:
        from executor.auto_mission_executor import auto_mission_executor_status
        data["auto_executor"] = auto_mission_executor_status()
    except Exception as e:
        data["auto_executor_error"] = str(e)

    try:
        from executor.auto_mission_scheduler import auto_mission_scheduler_status
        data["auto_scheduler"] = auto_mission_scheduler_status()
    except Exception as e:
        data["auto_scheduler_error"] = str(e)

    try:
        from executor.self_diagnosis import self_diagnosis_status
        data["diagnosis"] = self_diagnosis_status()
    except Exception as e:
        data["diagnosis_error"] = str(e)

    try:
        from executor.autonomous_repair import repair_status
        data["repair"] = repair_status()
    except Exception as e:
        data["repair_error"] = str(e)

    try:
        from executor.cloud_brain_backup import list_brain_backups
        data["backups"] = list_brain_backups()
    except Exception as e:
        data["backups_error"] = str(e)

    data["summary"] = {
        "pending_total": data.get("pending", {}).get("total", 0),
        "goals_active": data.get("goals", {}).get("active", 0),
        "missions_active": data.get("missions", {}).get("active", 0),
        "missions_blocked": data.get("missions", {}).get("blocked", 0),
        "repair_pending": data.get("repair", {}).get("pending", 0),
        "auto_executor_enabled": data.get("auto_executor", {}).get("enabled", False),
        "auto_scheduler_enabled": data.get("auto_scheduler", {}).get("state", {}).get("enabled", False),
        "diagnosis_ok": data.get("diagnosis", {}).get("report", {}).get("ok", data.get("diagnosis", {}).get("ok")),
        "backup_count": data.get("backups", {}).get("count", 0),
    }

    return data


def run_executive_command_cycle(trigger="command_center"):
    from executor.executive_loop_v2 import run_executive_loop_v2
    from executor.pending_review import pending_review_status

    result = run_executive_loop_v2(trigger)
    pending = pending_review_status()
    status = executive_command_center_status()

    return {
        "ok": True,
        "cycle": result,
        "pending": pending,
        "status": status,
        "time": time.time(),
    }
