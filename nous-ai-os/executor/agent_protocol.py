"""Structured contracts and integrity checks for multi-agent cycle outcomes.

Integrity checks establish that recorded data is internally consistent; they do not
claim that an agent's factual statements have been independently proven.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


PROTOCOL_VERSION = 1
ROLE_NAMES = ("planner", "guardian", "researcher", "builder", "reviewer")
SPECIALIST_ROLES = ("researcher", "builder")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def digest_payload(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _role_record(value: Any) -> dict[str, Any]:
    if value is None:
        return {"present": False, "status": "not_run", "sha256": None, "keys": []}
    if not isinstance(value, dict):
        return {
            "present": True,
            "status": "invalid",
            "sha256": digest_payload(value),
            "keys": [],
        }
    return {
        "present": True,
        "status": value.get("status", "unknown"),
        "sha256": digest_payload(value),
        "keys": sorted(str(key) for key in value.keys())[:100],
    }


def build_cycle_contract(output: dict[str, Any]) -> dict[str, Any]:
    """Create a compact, deterministic record of role outputs and execution gates."""
    priority = output.get("priority")
    action = priority.get("action") if isinstance(priority, dict) else None
    guardian = output.get("guardian")
    policy = guardian.get("policy") if isinstance(guardian, dict) else None
    guardian_allowed = (
        isinstance(guardian, dict)
        and guardian.get("status") == "completed"
        and isinstance(policy, dict)
        and policy.get("allowed") is True
    )
    execution = output.get("execution")
    execution = execution if isinstance(execution, dict) else {}
    roles = {name: _role_record(output.get(name)) for name in ROLE_NAMES}
    specialist_present = any(roles[name]["present"] for name in SPECIALIST_ROLES)
    checks = {
        "guardian_gate_consistent": (
            specialist_present == guardian_allowed
            if action in {"research_to_knowledge", "act", "recover_or_retry", "decide"}
            else not specialist_present
        ),
        "execution_status_known": execution.get("status") in {
            "blocked", "no_action", "completed", "failed"
        },
        "failed_specialist_is_reported": all(
            not roles[name]["present"]
            or roles[name]["status"] != "failed"
            or execution.get("status") == "failed"
            for name in SPECIALIST_ROLES
        ),
        "role_records_well_formed": all(
            isinstance(record, dict) and record.get("status") in {
                "not_run", "completed", "failed", "invalid", "unknown"
            }
            for record in roles.values()
        ),
    }
    return {
        "protocol_version": PROTOCOL_VERSION,
        "cycle_id": str(output.get("cycle_id") or ""),
        "integrity_scope": "structural_consistency_not_factual_verification",
        "roles": roles,
        "execution": {
            "action": action,
            "effective_action": output.get("effective_action"),
            "status": execution.get("status"),
            "reason": execution.get("reason"),
        },
        "checks": checks,
        "valid": all(checks.values()),
        "cycle_sha256": digest_payload({
            key: value for key, value in output.items()
            if key not in {"protocol_contract", "protocol_validation"}
        }),
    }


def validate_cycle_contract(contract: Any, output: dict[str, Any]) -> dict[str, Any]:
    """Recheck a contract against its cycle payload without claiming semantic truth."""
    if not isinstance(contract, dict) or contract.get("protocol_version") != PROTOCOL_VERSION:
        return {"ok": False, "error": "unsupported_or_invalid_contract"}
    expected_digest = digest_payload({
        key: value for key, value in output.items()
        if key not in {"protocol_contract", "protocol_validation"}
    })
    checks = contract.get("checks")
    if not isinstance(checks, dict):
        return {"ok": False, "error": "missing_contract_checks"}
    return {
        "ok": contract.get("valid") is True and contract.get("cycle_sha256") == expected_digest,
        "digest_matches": contract.get("cycle_sha256") == expected_digest,
        "checks": dict(checks),
        "scope": contract.get("integrity_scope"),
    }
