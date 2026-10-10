"""Deterministic verification of mission outcomes and completion evidence.

These checks verify consistency of recorded outputs; they do not establish that
an external system's claims are factually true unless that action supplies its
own independently checkable result.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from executor.mission_contracts import verify_execution_evidence


FAILURE_STATUSES = {"failed", "failure", "error", "blocked", "denied", "rejected"}


def _digest(value: Any) -> str:
    canonical = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def find_explicit_failure(value: Any, path: str = "result") -> list[dict[str, str]]:
    """Find explicit failure signals nested inside wrapper/action output."""
    failures: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if key in {"ok", "success"} and item is False:
                failures.append({"path": child_path, "reason": f"{key}_false"})
            elif key == "status" and isinstance(item, str) and item.strip().lower() in FAILURE_STATUSES:
                failures.append({"path": child_path, "reason": f"status_{item.strip().lower()}"})
            elif key == "error" and item not in (None, "", False, [], {}):
                failures.append({"path": child_path, "reason": "explicit_error"})
            if isinstance(item, (dict, list)):
                failures.extend(find_explicit_failure(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, (dict, list)):
                failures.extend(find_explicit_failure(item, f"{path}[{index}]"))
    return failures


def verify_task_completion(task: Any) -> dict[str, Any]:
    """Verify a task's stored result against its execution evidence."""
    if not isinstance(task, dict):
        return {"status": "needs_review", "ok": False, "reason": "task_record_invalid"}

    status = task.get("status")
    if status == "failed":
        return {"status": "failed", "ok": False, "reason": "task_execution_failed"}
    if status != "done":
        return {"status": "needs_review", "ok": False, "reason": "task_not_done"}

    result = task.get("result")
    if not isinstance(result, dict):
        return {"status": "needs_review", "ok": False, "reason": "result_missing_or_invalid"}

    failures = find_explicit_failure(result)
    if failures:
        return {
            "status": "failed",
            "ok": False,
            "reason": "explicit_failure_in_result",
            "failures": failures[:20],
        }

    evidence = task.get("execution_evidence")
    evidence_check = verify_execution_evidence(evidence)
    if not evidence_check.get("ok"):
        return {
            "status": "needs_review",
            "ok": False,
            "reason": "execution_evidence_invalid",
            "evidence_check": evidence_check,
        }

    payload = task.get("payload", {})
    if not isinstance(payload, dict):
        return {"status": "needs_review", "ok": False, "reason": "task_payload_invalid"}

    checks = {
        "task_id_matches": str(evidence.get("task_id")) == str(task.get("id")),
        "execution_id_matches": evidence.get("execution_id") == task.get("execution_id"),
        "action_matches": evidence.get("action") == task.get("action"),
        "payload_matches": evidence.get("payload_sha256") == _digest(payload),
        "result_matches": evidence.get("result_sha256") == _digest(result),
        "result_reports_success": evidence.get("result_ok") is True,
    }
    if not all(checks.values()):
        return {
            "status": "needs_review",
            "ok": False,
            "reason": "task_and_evidence_mismatch",
            "checks": checks,
        }

    return {
        "status": "verified",
        "ok": True,
        "reason": "recorded_outcome_and_evidence_consistent",
        "checks": checks,
    }


def verify_mission_completion(mission: Any) -> dict[str, Any]:
    """Assess whether every task has a consistent, verifiable completion record."""
    if not isinstance(mission, dict):
        return {"status": "needs_review", "ok": False, "reason": "mission_record_invalid"}

    tasks = mission.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return {"status": "needs_review", "ok": False, "reason": "mission_has_no_tasks"}

    assessments = []
    for task in tasks:
        assessment = verify_task_completion(task)
        assessments.append({
            "task_id": task.get("id") if isinstance(task, dict) else None,
            **assessment,
        })

    if all(item["status"] == "verified" for item in assessments):
        status = "completed"
        reason = "all_task_outcomes_verified"
    elif any(item["status"] == "failed" for item in assessments):
        status = "failed"
        reason = "one_or_more_tasks_failed"
    else:
        status = "needs_review"
        reason = "completion_evidence_incomplete_or_inconsistent"

    return {
        "status": status,
        "ok": status == "completed",
        "reason": reason,
        "task_count": len(assessments),
        "verified_count": sum(item["status"] == "verified" for item in assessments),
        "failed_count": sum(item["status"] == "failed" for item in assessments),
        "review_count": sum(item["status"] == "needs_review" for item in assessments),
        "tasks": assessments,
    }
