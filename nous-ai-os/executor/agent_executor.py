import time
from executor.agent_planner import make_steps
from executor.research_agent import web_search
from executor.code_forge import forge_plugin
from executor.git_agent import git_checkpoint
from executor.memory import save

def solve_goal(goal):
    steps = make_steps(goal)
    result = {
        "goal": goal,
        "steps": steps,
        "actions": [],
        "status": "running"
    }

    if any(w in goal.lower() for w in ["plugin", "calculator", "κώδικ", "code"]):
        forged = forge_plugin(goal)
        result["actions"].append({"code_forge": forged})

    if any(w in goal.lower() for w in ["ψάξε", "research", "internet", "online"]):
        research = web_search(goal)
        result["actions"].append({"research": research})

    save({
        "event": "agent_solve",
        "goal": goal,
        "result": result
    })

    result["status"] = "completed"
    return result

def solve_and_checkpoint(goal):
    result = solve_goal(goal)
    checkpoint = git_checkpoint("NOUS agent solved goal checkpoint")
    result["checkpoint"] = checkpoint
    return result
