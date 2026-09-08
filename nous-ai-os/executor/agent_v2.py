from executor.memory_store import get_mem, set_mem
from executor.plugin_registry import run_plugin

def planner(goal):

    history = get_mem("history", [])

    plan = {
        "goal": goal,
        "steps": [
            "analyze",
            "execute_plugins",
            "store_result"
        ]
    }

    history.append(plan)
    set_mem("history", history)

    return plan


def executor(goal):

    if "plugin:" in goal:
        name = goal.replace("plugin:", "").strip()
        return run_plugin(name)

    return {
        "result": f"executed goal: {goal}"
    }


def run(goal):

    plan = planner(goal)
    result = executor(goal)

    return {
        "plan": plan,
        "result": result
    }
