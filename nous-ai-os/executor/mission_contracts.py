"""Immutable mission-plan fingerprints and truthful execution evidence."""
from __future__ import annotations
import hashlib
import json
from typing import Any

PLAN_VERSION = 1

def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)

def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()

def _plan_fields(task: dict[str, Any]) -> dict[str, Any]:
    return {"id": task.get("id"), "title": task.get("title"), "action": task.get("action"), "payload": task.get("payload", {}), "requires_approval": bool(task.get("requires_approval"))}

def build_plan_contract(tasks: Any) -> dict[str, Any]:
    """Fingerprint immutable task intent, excluding mutable runtime state."""
    if not isinstance(tasks, list) or any(not isinstance(task, dict) for task in tasks):
        return {"version": PLAN_VERSION, "valid": False, "error": "invalid_task_list"}
    fields = [_plan_fields(task) for task in tasks]
    ids = [str(task.get("id")) for task in fields]
    valid = len(ids) == len(set(ids)) and all(task.get("id") is not None for task in fields)
    return {"version": PLAN_VERSION, "valid": valid, "task_count": len(fields), "plan_sha256": _digest(fields), "task_ids": ids}

def verify_plan_contract(contract: Any, tasks: Any) -> dict[str, Any]:
    if not isinstance(contract, dict) or contract.get("version") != PLAN_VERSION:
        return {"ok": False, "error": "missing_or_unsupported_plan_contract"}
    current = build_plan_contract(tasks)
    matches = current.get("valid") is True and contract.get("valid") is True and current.get("plan_sha256") == contract.get("plan_sha256") and current.get("task_ids") == contract.get("task_ids") and current.get("task_count") == contract.get("task_count")
    return {"ok": matches, "plan_sha256": current.get("plan_sha256"), "error": None if matches else "mission_plan_changed"}

def build_execution_evidence(task: dict[str, Any], result: dict[str, Any], execution_id: str) -> dict[str, Any]:
    """Bind the claimed action, payload, outcome and claim ID into a verifiable record."""
    evidence = {"version": PLAN_VERSION, "task_id": task.get("id"), "execution_id": str(execution_id), "action": task.get("action"), "payload_sha256": _digest(task.get("payload", {})), "result_sha256": _digest(result), "result_ok": result.get("ok") is True, "task_status": task.get("status")}
    evidence["evidence_sha256"] = _digest(evidence)
    return evidence

def verify_execution_evidence(evidence: Any) -> dict[str, Any]:
    if not isinstance(evidence, dict) or evidence.get("version") != PLAN_VERSION:
        return {"ok": False, "error": "missing_or_unsupported_execution_evidence"}
    payload = {key: value for key, value in evidence.items() if key != "evidence_sha256"}
    matches = evidence.get("evidence_sha256") == _digest(payload)
    consistent = bool(evidence.get("execution_id")) and evidence.get("task_id") is not None and evidence.get("task_status") == ("done" if evidence.get("result_ok") else "failed")
    return {"ok": matches and consistent, "digest_matches": matches, "outcome_consistent": consistent}
