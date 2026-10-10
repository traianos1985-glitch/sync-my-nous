"""Explicit allowlist for actions that have been verified against runtime reality."""
import time

from executor.reality_gate import reality_status
from executor.research_browser_agent import research_query, read_url
from executor.android_control import android_open_url, android_notify
from executor.code_assistant import code_health
from executor.git_workflow import git_workflow_status
from executor.app_factory_v2 import create_app_from_idea
from executor.agent_journal import write_journal
from executor.runtime_governance import (
    ActionPayloadError,
    result_succeeded,
    safe_payload_summary,
    validate_action_payload,
)

REAL_ACTIONS = {
    "internet_search",
    "browser_read",
    "android_open_url",
    "android_notify",
    "git_status",
    "code_health",
    "app_factory",
}


def available_real_actions():
    r = reality_status()
    return {
        "internet_search": bool(r["internet"]["real"]),
        "browser_read": bool(r["browser_read"]["real"]),
        "android_open_url": bool(r["android"]["real_intents"]),
        "android_notify": True,
        "git_status": bool(r["git"]["real"]),
        "code_health": bool(r["code"]["real"]),
        "app_factory": bool(r["app_factory"]["real"]),
        "android_gestures": bool(r["android"]["real_gestures"]),
        "real_hosting_deploy": False,
        "browser_login": False,
        "time": time.time(),
    }


def run_real_action(action, payload=None):
    """Validate and run one explicitly allowlisted action with truthful outcomes."""
    if not isinstance(action, str) or action not in REAL_ACTIONS:
        return {"ok": False, "error": "unknown_action", "allowed_actions": sorted(REAL_ACTIONS)}

    try:
        payload = validate_action_payload({} if payload is None else payload)
    except ActionPayloadError as exc:
        return {"ok": False, "error": str(exc), "action": action}

    allowed = available_real_actions()
    if not allowed.get(action, False):
        return {
            "ok": False,
            "error": "action_not_real_available",
            "action": action,
            "available": allowed,
        }

    try:
        if action == "internet_search":
            result = research_query(payload.get("query", ""), learn=bool(payload.get("learn", False)))
        elif action == "browser_read":
            result = read_url(payload.get("url", ""), learn=bool(payload.get("learn", False)))
        elif action == "android_open_url":
            result = android_open_url(payload.get("url", ""))
        elif action == "android_notify":
            result = android_notify(payload.get("title", "ΝΟΥΣ AI"), payload.get("message", "Ο ΝΟΥΣ είναι ενεργός"))
        elif action == "git_status":
            result = git_workflow_status()
        elif action == "code_health":
            result = code_health()
        elif action == "app_factory":
            result = create_app_from_idea(payload.get("idea", ""))
        else:  # Defensive even though REAL_ACTIONS is explicit.
            return {"ok": False, "error": "not_implemented", "action": action}
    except Exception as exc:
        failure = {
            "ok": False,
            "action": action,
            "error": "action_execution_exception",
            "detail": type(exc).__name__,
            "time": time.time(),
        }
        try:
            write_journal("real_action_failed", {
                "action": action,
                "payload_summary": safe_payload_summary(payload),
                "error": type(exc).__name__,
            })
            failure["audit_recorded"] = True
        except Exception:
            failure["audit_recorded"] = False
        return failure

    succeeded = result_succeeded(result)
    output = {
        "ok": succeeded,
        "action": action,
        "payload_summary": safe_payload_summary(payload),
        "result": result,
        "time": time.time(),
    }
    try:
        write_journal("real_action_executed" if succeeded else "real_action_failed", {
            "action": action,
            "payload_summary": output["payload_summary"],
            "ok": succeeded,
            "result_type": type(result).__name__,
        })
        output["audit_recorded"] = True
    except Exception:
        # Report audit degradation without pretending it was recorded.
        output["audit_recorded"] = False
        output["audit_error"] = "journal_unavailable"
    return output


def real_actions_status():
    return {
        "available": available_real_actions(),
        "executable_actions": sorted(REAL_ACTIONS),
        "note": "Only explicitly allowlisted actions proven by reality_gate are executable.",
        "time": time.time(),
    }
