import time

from executor.curiosity_agent import load_queue, load_knowledge, mark_learned, knowledge_status
from executor.research_browser_agent import research_query, read_url
from executor.agent_journal import write_journal
from executor.memory import save


def _next_topic():
    items = [x for x in load_queue() if x.get("status") == "open"]
    if not items:
        return None
    return sorted(items, key=lambda x: x.get("priority", 5))[0]


def internet_learn_topic(topic=None, query=None):
    if not topic:
        item = _next_topic()
        if not item:
            return {
                "idle": True,
                "reason": "no_open_topics",
                "knowledge": knowledge_status(),
            }
        topic = item.get("topic")

    q = query or str(topic)

    research = research_query(q, learn=False)
    summary = str(research.get("result", ""))[:3000]

    learned = mark_learned(
        topic=topic,
        summary=summary,
        source="internet_learning_pipeline"
    )

    output = {
        "ok": True,
        "topic": topic,
        "query": q,
        "research": research,
        "learned": learned,
        "knowledge": knowledge_status(),
        "time": time.time(),
    }

    write_journal("internet_topic_learned", output)
    save({"event": "internet_topic_learned", "topic": topic})
    return output


def internet_learn_url(url, topic=None):
    result = read_url(url, learn=False)
    t = topic or url

    learned = mark_learned(
        topic=t,
        summary=str(result.get("content", ""))[:4000],
        source="internet_url_learning_pipeline"
    )

    output = {
        "ok": True,
        "url": url,
        "topic": t,
        "read": result,
        "learned": learned,
        "knowledge": knowledge_status(),
        "time": time.time(),
    }

    write_journal("internet_url_learned", output)
    save({"event": "internet_url_learned", "topic": t, "url": url})
    return output


def internet_learning_status():
    return {
        "time": time.time(),
        "knowledge": knowledge_status(),
        "next_topic": _next_topic(),
        "learned_items": len(load_knowledge()),
    }
