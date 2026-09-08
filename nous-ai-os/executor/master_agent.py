import time

from executor.decision_engine import decide_next_action
from executor.real_action_executor import execute_decision
from executor.real_research_engine import research_to_knowledge, research_status
from executor.goal_progress import goal_progress_summary
from executor.project_progress import project_summary
from executor.task_queue import list_queue
from executor.learning_engine import learning_status
from executor.battery_guard import battery_guard
from executor.guardian_policy import check_action
from executor.agent_journal import write_journal


def master_state():
    return {
        "time": time.time(),
        "battery": battery_guard(),
        "goals": goal_progress_summary(),
        "projects": project_summary(),
        "queue": list_queue(),
        "learning": learning_status(),
        "research": research_status(),
    }


def choose_master_priority():
    state = master_state()
    battery = state["battery"]
    queue = state["queue"]
    knowledge = state["learning"]["knowledge"]

    pending = [x for x in queue if x.get("status") == "pending"]
    failed = [x for x in queue if x.get("status") == "failed"]

    if int(battery.get("level", 100)) < 25 and str(battery.get("plugged", "")).upper() == "UNPLUGGED":
        return {
            "role": "guardian",
            "action": "pause",
            "reason": "low_battery",
            "state": state,
        }

    if failed:
        return {
            "role": "executor",
            "action": "recover_or_retry",
            "reason": "failed_tasks_exist",
            "state": state,
        }

    if pending:
        return {
            "role": "executor",
            "action": "act",
            "reason": "pending_task_exists",
            "state": state,
        }

    if knowledge.get("open", 0) > 0:
        return {
            "role": "researcher",
            "action": "research_to_knowledge",
            "reason": "open_learning_topics",
            "state": state,
        }

    return {
        "role": "planner",
        "action": "decide",
        "reason": "default_decision_cycle",
        "state": state,
    }


def master_cycle(real_research=False):
    priority = choose_master_priority()
    action = priority.get("action")

    policy = check_action("act" if action in ["act", "recover_or_retry", "decide"] else action)

    if not policy.get("allowed"):
        output = {
            "executed": False,
            "priority": priority,
            "policy": policy,
        }
        write_journal("master_cycle_blocked", output)
        return output

    if action == "pause":
        result = {"paused": True, "reason": priority.get("reason")}

    elif action == "research_to_knowledge":
        if real_research:
            result = research_to_knowledge()
        else:
            result = {
                "planned": True,
                "reason": "real_research_disabled_for_safe_cycle",
                "research": research_status(),
            }

    else:
        decision = decide_next_action()
        result = execute_decision(decision)

    output = {
        "executed": True,
        "priority": priority,
        "policy": policy,
        "result": result,
        "time": time.time(),
    }

    write_journal("master_cycle_executed", output)
    return output
