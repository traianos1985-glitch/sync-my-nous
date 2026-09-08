import time

from executor.curiosity_agent import curiosity_cycle, knowledge_status, active_learning_topics
from executor.knowledge_research import learning_cycle
from executor.memory import save


def learning_status():
    return {
        "time": time.time(),
        "knowledge": knowledge_status(),
        "active_learning_topics": active_learning_topics(),
    }


def learning_run(max_topics=1, research=False):
    curiosity = curiosity_cycle()

    result = {
        "curiosity": curiosity,
        "learning": None,
        "status": learning_status(),
    }

    if research:
        result["learning"] = learning_cycle(max_topics=max_topics)

    save({
        "event": "learning_engine_run",
        "research": research,
        "max_topics": max_topics,
        "status": result["status"],
    })

    return result


def auto_learning_cycle():
    """
    Safe automatic learning cycle.
    It updates curiosity topics but does not perform internet research automatically.
    Real web research remains admin-triggered.
    """
    result = learning_run(max_topics=1, research=False)
    save({
        "event": "auto_learning_cycle",
        "open": result.get("status", {}).get("knowledge", {}).get("open"),
    })
    return result
