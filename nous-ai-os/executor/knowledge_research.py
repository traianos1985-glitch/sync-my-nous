import time

from executor.curiosity_agent import load_queue, mark_learned, knowledge_status
from executor.research_agent import web_search
from executor.memory import save


def next_open_topic():
    queue = load_queue()
    open_items = [x for x in queue if x.get("status") == "open"]

    if not open_items:
        return None

    open_items = sorted(open_items, key=lambda x: x.get("priority", 5))
    return open_items[0]


def research_topic(topic):
    query = f"ψάξε {topic}"
    result = web_search(query)

    summary = str(result)
    if len(summary) > 1500:
        summary = summary[:1500] + "..."

    learned = mark_learned(
        topic=topic,
        summary=summary,
        source="web_search"
    )

    event = {
        "event": "knowledge_research_done",
        "topic": topic,
        "time": time.time(),
        "learned": learned,
    }
    save(event)

    return {
        "topic": topic,
        "query": query,
        "result": result,
        "learned": learned,
    }


def research_next_topic():
    item = next_open_topic()

    if not item:
        return {
            "idle": True,
            "reason": "no_open_topics",
            "knowledge": knowledge_status(),
        }

    return research_topic(item.get("topic"))


def learning_cycle(max_topics=1):
    results = []

    for _ in range(int(max_topics)):
        result = research_next_topic()
        results.append(result)

        if result.get("idle"):
            break

    return {
        "ran": len([x for x in results if not x.get("idle")]),
        "results": results,
        "knowledge": knowledge_status(),
    }
