import time

from executor.master_agent import master_state, choose_master_priority
from executor.decision_engine import decide_next_action
from executor.real_research_engine import research_status, research_to_knowledge
from executor.code_assistant import code_health, code_advice
from executor.app_factory_v2 import app_factory_status
from executor.guardian_policy import check_action
from executor.agent_journal import write_journal


def planner_agent(goal=""):
    decision = decide_next_action()
    return {
        "role": "planner",
        "goal": goal,
        "decision": decision,
        "time": time.time(),
    }


def researcher_agent(topic=None, real=False):
    status = research_status()

    if real:
        result = research_to_knowledge(topic)
    else:
        result = {
            "planned": True,
            "reason": "real_research_disabled",
            "status": status,
        }

    return {
        "role": "researcher",
        "topic": topic,
        "real": real,
        "result": result,
        "time": time.time(),
    }


def builder_agent(request=""):
    return {
        "role": "builder",
        "request": request,
        "app_factory": app_factory_status(),
        "code": code_health(),
        "time": time.time(),
    }


def reviewer_agent():
    return {
        "role": "reviewer",
        "code_advice": code_advice(),
        "time": time.time(),
    }


def guardian_agent(action="act", payload=None):
    return {
        "role": "guardian",
        "policy": check_action(action, payload or {}),
        "time": time.time(),
    }


def team_status():
    return {
        "time": time.time(),
        "master": master_state(),
        "priority": choose_master_priority(),
        "roles": ["planner", "researcher", "builder", "reviewer", "guardian"],
    }


def team_cycle(real_research=False):
    priority = choose_master_priority()
    action = priority.get("action")

    output = {
        "time": time.time(),
        "priority": priority,
        "planner": planner_agent(),
        "guardian": guardian_agent(action),
        "researcher": None,
        "builder": None,
        "reviewer": None,
    }

    if action == "research_to_knowledge":
        output["researcher"] = researcher_agent(real=real_research)

    elif action in ["act", "recover_or_retry", "decide"]:
        output["builder"] = builder_agent(action)

    output["reviewer"] = reviewer_agent()

    write_journal("multi_agent_team_cycle", output)
    return output
