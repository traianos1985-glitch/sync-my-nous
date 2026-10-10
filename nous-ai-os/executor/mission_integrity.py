"""Read-only consistency audit for persisted NOUS mission state.

The audit never repairs or executes work. Findings are advisory integrity signals;
they do not prove that an external action's claimed result is factually true.
"""
from __future__ import annotations

import math
import time
from typing import Any

from executor.mission_completion import verify_mission_completion, verify_task_completion
from executor.mission_contracts import verify_plan_contract


KNOWN_MISSION_STATUSES = {"active", "blocked", "done", "failed", "cancelled"}
KNOWN_TASK_STATUSES = {
    "pending", "running", "waiting_approval", "done", "failed",
    "blocked", "rejected", "needs_review", "cancelled",
}


def audit_missions(missions: Any, now: float | None = None, stale_after: float = 900) -> dict[str, Any]:
    """Report malformed records, conflicting states, stale claims and bad evidence."""
    try:
        now = time.time() if now is None else float(now)
        if not math.isfinite(now):
            raise ValueError("non-finite timestamp")
    except (TypeError, ValueError, OverflowError):
        now = time.time()
    try:
        stale_after = max(1.0, float(stale_after))
    except (TypeError, ValueError, OverflowError):
        stale_after = 900.0
    issues: list[dict[str, Any]] = []
    if not isinstance(missions, list):
        return {
            "ok": False, "status": "degraded", "mission_count": 0,
            "issue_count": 1,
            "issues": [{"code": "mission_store_not_a_list", "severity": "error"}],
        }

    mission_ids: set[str] = set()
    for index, mission in enumerate(missions):
        prefix = {"mission_index": index}
        if not isinstance(mission, dict):
            issues.append({**prefix, "code": "mission_record_not_object", "severity": "error"})
            continue

        mission_id = mission.get("id")
        key = str(mission_id)
        if mission_id is None:
            issues.append({**prefix, "code": "mission_id_missing", "severity": "error"})
        elif key in mission_ids:
            issues.append({**prefix, "mission_id": mission_id, "code": "duplicate_mission_id", "severity": "error"})
        mission_ids.add(key)

        mission_status = mission.get("status")
        if not isinstance(mission_status, str) or mission_status not in KNOWN_MISSION_STATUSES:
            issues.append({**prefix, "mission_id": mission_id, "code": "unknown_mission_status", "severity": "error"})
        tasks = mission.get("tasks")
        if not isinstance(tasks, list):
            issues.append({**prefix, "mission_id": mission_id, "code": "tasks_not_a_list", "severity": "error"})
            continue

        task_ids: set[str] = set()
        running = []
        done_tasks = []
        for task_index, task in enumerate(tasks):
            task_prefix = {**prefix, "mission_id": mission_id, "task_index": task_index}
            if not isinstance(task, dict):
                issues.append({**task_prefix, "code": "task_record_not_object", "severity": "error"})
                continue
            task_id = task.get("id")
            task_key = str(task_id)
            if task_id is None:
                issues.append({**task_prefix, "code": "task_id_missing", "severity": "error"})
            elif task_key in task_ids:
                issues.append({**task_prefix, "task_id": task_id, "code": "duplicate_task_id", "severity": "error"})
            task_ids.add(task_key)

            status = task.get("status")
            if not isinstance(status, str) or status not in KNOWN_TASK_STATUSES:
                issues.append({**task_prefix, "code": "unknown_task_status", "severity": "error"})
            if status == "running":
                running.append(task)
                try:
                    started = float(task.get("started") or 0)
                except (TypeError, ValueError, OverflowError):
                    started = 0
                if started <= 0 or started > now or now - started >= stale_after:
                    issues.append({**task_prefix, "code": "stale_or_invalid_running_claim", "severity": "warning"})
            if status == "done":
                done_tasks.append(task)
                try:
                    check = verify_task_completion(task)
                except Exception as exc:
                    check = {"status": "invalid", "reason": f"verification_error:{type(exc).__name__}"}
                if check.get("status") != "verified":
                    issues.append({
                        **task_prefix,
                        "code": "done_task_evidence_invalid",
                        "severity": "error",
                        "reason": check.get("reason"),
                    })

        if len(running) > 1:
            issues.append({**prefix, "mission_id": mission_id, "code": "multiple_running_tasks", "severity": "error"})
        if mission_status == "done":
            try:
                completion = verify_mission_completion(mission)
            except Exception as exc:
                completion = {"status": "invalid", "reason": f"verification_error:{type(exc).__name__}"}
            if completion.get("status") != "completed":
                issues.append({
                    **prefix, "mission_id": mission_id,
                    "code": "done_mission_not_verified", "severity": "error",
                    "reason": completion.get("reason"),
                })
            if any(not isinstance(task.get("status"), str) or task.get("status") != "done" for task in tasks if isinstance(task, dict)):
                issues.append({**prefix, "mission_id": mission_id, "code": "done_mission_has_incomplete_tasks", "severity": "error"})
        elif mission_status == "active" and any(isinstance(task.get("status"), str) and task.get("status") in {"failed", "blocked", "needs_review", "rejected", "cancelled"} for task in tasks if isinstance(task, dict)):
            issues.append({**prefix, "mission_id": mission_id, "code": "active_mission_contains_terminal_task", "severity": "warning"})

        contract = mission.get("plan_contract")
        if contract is not None:
            try:
                plan_check = verify_plan_contract(contract, tasks)
            except Exception as exc:
                plan_check = {"ok": False, "error": f"verification_error:{type(exc).__name__}"}
            if not plan_check.get("ok"):
                issues.append({
                    **prefix, "mission_id": mission_id,
                    "code": "mission_plan_contract_mismatch", "severity": "error",
                    "reason": plan_check.get("error"),
                })

    errors = sum(issue["severity"] == "error" for issue in issues)
    warnings = sum(issue["severity"] == "warning" for issue in issues)
    return {
        "ok": not issues,
        "status": "healthy" if not issues else "degraded",
        "mission_count": len(missions),
        "issue_count": len(issues),
        "error_count": errors,
        "warning_count": warnings,
        "issues": issues[:200],
        "truncated": len(issues) > 200,
        "checked_at": now,
    }
