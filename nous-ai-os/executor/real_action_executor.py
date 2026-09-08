import time

from executor.decision_engine import decide_next_action
from executor.goal_executor import seed_goals_to_queue, run_next_task
from executor.task_queue import retry_failed
from executor.learning_engine import auto_learning_cycle
from executor.agent_journal import write_journal
from executor.memory import save


def execute_decision(decision=None):
    if decision is None:
        decision = decide_next_action()

    action = decision.get("action")

    if action == "pause":
        result = {
            "executed": False,
            "action": action,
            "reason": decision.get("reason"),
        }

    elif action == "recover_failed_tasks":
        result = {
            "executed": True,
            "action": action,
            "result": retry_failed(),
        }

    elif action == "run_next_queue_task":
        result = {
            "executed": True,
            "action": action,
            "result": run_next_task(),
        }

    elif action == "seed_goal_task":
        result = {
            "executed": True,
            "action": action,
            "result": seed_goals_to_queue(),
        }

    elif action == "learning_cycle":
        result = {
            "executed": True,
            "action": action,
            "result": auto_learning_cycle(),
        }

    else:
        result = {
            "executed": False,
            "action": action,
            "reason": "idle_or_unknown_action",
        }

    output = {
        "time": time.time(),
        "decision": decision,
        "result": result,
    }

    write_journal("decision_executed", output)
    save({"event": "real_action_executor", "output": output})
    return output


def agent_act_cycle():
    decision = decide_next_action()
    return execute_decision(decision)
