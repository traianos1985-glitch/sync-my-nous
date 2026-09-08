from executor.plugin_registry import run_plugin

def decide(goal):

    if "plugin:" in goal:
        return "create_plugin"

    if "evolve" in goal:
        return "improve_system"

    return "idle"


# FIX: τώρα δέχεται context επίσης (για hybrid system)
def act(goal, context=None):

    action = decide(goal)

    if action == "create_plugin":
        return run_plugin(goal.replace("plugin:", "").strip())

    if action == "improve_system":
        return {
            "status": "evolving",
            "context_used": context is not None
        }

    return {
        "status": "executed",
        "goal": goal,
        "context": context
    }
