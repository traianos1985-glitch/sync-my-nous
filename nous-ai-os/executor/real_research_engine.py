import time

from executor.knowledge_research import next_open_topic, research_topic
from executor.curiosity_agent import knowledge_status, load_knowledge
from executor.agent_journal import write_journal
from executor.guardian_policy import check_action


def research_to_knowledge(topic=None):
    policy = check_action("research_query")

    if not policy.get("allowed"):
        return {"ok": False, "policy": policy}

    if not topic:
        item = next_open_topic()
        if not item:
            return {
                "idle": True,
                "reason": "no_open_topics",
                "knowledge": knowledge_status(),
            }
        topic = item.get("topic")

    result = research_topic(topic)

    output = {
        "ok": True,
        "topic": topic,
        "result": result,
        "knowledge": knowledge_status(),
        "time": time.time(),
    }

    write_journal("real_research_to_knowledge", output)
    return output


def learned_items():
    return load_knowledge()


def research_status():
    return {
        "knowledge": knowledge_status(),
        "learned_items": len(load_knowledge()),
        "next_topic": next_open_topic(),
        "time": time.time(),
    }
