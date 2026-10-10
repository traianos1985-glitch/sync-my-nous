"""Governed multi-agent coordination with explicit outcomes and fail-closed policy gates."""
import time
from typing import Any, Callable

from executor.master_agent import master_state, choose_master_priority
from executor.decision_engine import decide_next_action
from executor.real_research_engine import research_status, research_to_knowledge
from executor.code_assistant import code_health, code_advice
from executor.app_factory_v2 import app_factory_status
from executor.guardian_policy import check_action
from executor.agent_journal import write_journal


def planner_agent(goal=""):
    decision = decide_next_action()
    return {"role": "planner", "goal": goal, "decision": decision, "time": time.time()}


def researcher_agent(topic=None, real=False):
    status = research_status()
    if real:
        result = research_to_knowledge(topic)
    else:
        result = {"planned": True, "reason": "real_research_disabled", "status": status}
    return {"role": "researcher", "topic": topic, "real": real, "result": result, "time": time.time()}


def builder_agent(request=""):
    return {
        "role": "builder",
        "request": request,
        "app_factory": app_factory_status(),
        "code": code_health(),
        "time": time.time(),
    }


def reviewer_agent():
    return {"role": "reviewer", "code_advice": code_advice(), "time": time.time()}


def guardian_agent(action="act", payload=None):
    return {"role": "guardian", "policy": check_action(action, payload or {}), "time": time.time()}


def team_status():
    return {
        "time": time.time(),
        "master": master_state(),
        "priority": choose_master_priority(),
        "roles": ["planner", "researcher", "builder", "reviewer", "guardian"],
    }


def _run_role(role: str, callback: Callable[[], Any]) -> dict[str, Any]:
    """Turn exceptions and malformed role outputs into explicit, bounded outcomes."""
    try:
        result = callback()
        if not isinstance(result, dict):
            return {"role": role, "status": "failed", "error": "invalid_role_result"}
        return {**result, "status": "completed"}
    except Exception as exc:
        return {
            "role": role,
            "status": "failed",
            "error": f"{type(exc).__name__}: {str(exc)[:240]}",
            "time": time.time(),
        }


def _policy_action(action):
    """Map internal coordinator labels to explicit guardian capabilities."""
    if action == "research_to_knowledge":
        return "research_query"
    if action in {"act", "recover_or_retry", "decide"}:
        return "act"
    return action if isinstance(action, str) and action else "unknown_action"


def team_cycle(real_research=False):
    priority = choose_master_priority()
    action = priority.get("action") if isinstance(priority, dict) else None
    effective_action = _policy_action(action)
    policy_result = _run_role("guardian", lambda: guardian_agent(effective_action))
    policy = policy_result.get("policy")
    allowed = policy_result.get("status") == "completed" and isinstance(policy, dict) and policy.get("allowed") is True

    output = {
        "time": time.time(),
        "priority": priority,
        "effective_action": effective_action,
        "planner": _run_role("planner", planner_agent),
        "guardian": policy_result,
        "researcher": None,
        "builder": None,
        "reviewer": None,
        "execution": {
            "status": "blocked" if not allowed else "no_action",
            "action": action,
            "reason": "guardian_denied_or_failed" if not allowed else "no_specialist_for_action",
        },
    }

    # A policy result is a hard gate, not merely advisory metadata.
    if allowed and action == "research_to_knowledge":
        result = _run_role("researcher", lambda: researcher_agent(real=real_research))
        output["researcher"] = result
        output["execution"] = {
            "status": result["status"],
            "action": action,
            "reason": "research_role_finished" if result["status"] == "completed" else "research_role_failed",
        }
    elif allowed and action in {"act", "recover_or_retry", "decide"}:
        result = _run_role("builder", lambda: builder_agent(action))
        output["builder"] = result
        output["execution"] = {
            "status": result["status"],
            "action": action,
            "reason": "builder_role_finished" if result["status"] == "completed" else "builder_role_failed",
        }

    output["reviewer"] = _run_role("reviewer", reviewer_agent)
    try:
        write_journal("multi_agent_team_cycle", output)
    except Exception as exc:
        # Preserve the actual execution outcome while surfacing the audit failure.
        output["journal_error"] = f"{type(exc).__name__}: {str(exc)[:240]}"
    return output
