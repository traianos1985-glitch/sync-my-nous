import json
import os
import time
import re

from executor.personal_agent import load_db
from executor.memory import load as load_memory

QUEUE_FILE = "data/knowledge_queue.json"
BASE_FILE = "data/knowledge_base.json"


SEED_TOPICS = [
    {
        "topic": "Greek NLP",
        "reason": "review quality improvement",
        "priority": 2,
    },
    {
        "topic": "AI agents",
        "reason": "core NOUS goal",
        "priority": 1,
    },
    {
        "topic": "Android automation",
        "reason": "NOUS runs on Android and Termux",
        "priority": 2,
    },
    {
        "topic": "Local LLM",
        "reason": "future local intelligence",
        "priority": 3,
    },
]


KEYWORD_TOPICS = {
    "agent": "AI agents",
    "ai agent": "AI agents",
    "νους": "AI agents",
    "autonomy": "Autonomous agents",
    "αυτονομ": "Autonomous agents",
    "android": "Android automation",
    "termux": "Android automation",
    "flask": "Python Flask",
    "python": "Python",
    "plugin": "Plugin systems",
    "scheduler": "Schedulers",
    "schedule": "Schedulers",
    "memory": "Long-term memory",
    "μνήμη": "Long-term memory",
    "greek": "Greek NLP",
    "ελλην": "Greek NLP",
    "llm": "Local LLM",
    "sdr": "SDR signal analysis",
    "rf": "RF signal analysis",
}


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except Exception:
        return default


def _save_json(path, data):
    os.makedirs("data", exist_ok=True)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def load_queue():
    return _load_json(QUEUE_FILE, [])


def save_queue(items):
    _save_json(QUEUE_FILE, items)


def load_knowledge():
    return _load_json(BASE_FILE, [])


def save_knowledge(items):
    _save_json(BASE_FILE, items)


def normalize_topic(topic):
    topic = str(topic).strip()
    topic = re.sub(r"\s+", " ", topic)
    return topic


def topic_exists(topic, queue=None, knowledge=None):
    q = queue if queue is not None else load_queue()
    k = knowledge if knowledge is not None else load_knowledge()
    target = normalize_topic(topic).lower()

    for item in q:
        if normalize_topic(item.get("topic", "")).lower() == target:
            return True

    for item in k:
        if normalize_topic(item.get("topic", "")).lower() == target:
            return True

    return False


def add_topic(topic, reason="manual", priority=5, source="curiosity"):
    topic = normalize_topic(topic)
    queue = load_queue()
    knowledge = load_knowledge()

    if not topic:
        return {"created": False, "reason": "empty_topic"}

    if topic_exists(topic, queue, knowledge):
        return {"created": False, "reason": "duplicate", "topic": topic}

    item = {
        "id": int(time.time_ns()),
        "topic": topic,
        "reason": reason,
        "priority": int(priority),
        "source": source,
        "status": "open",
        "created": time.time(),
        "updated": time.time(),
    }

    queue.append(item)
    save_queue(queue)
    return {"created": True, "item": item}


def mark_learned(topic, summary="", source="manual"):
    topic = normalize_topic(topic)
    queue = load_queue()
    knowledge = load_knowledge()

    matched = None
    for item in queue:
        if normalize_topic(item.get("topic", "")).lower() == topic.lower():
            item["status"] = "learned"
            item["updated"] = time.time()
            matched = item

    knowledge_item = {
        "id": int(time.time_ns()),
        "topic": topic,
        "summary": str(summary).strip(),
        "source": source,
        "created": time.time(),
    }
    knowledge.append(knowledge_item)

    save_queue(queue)
    save_knowledge(knowledge)

    return {
        "marked": matched is not None,
        "knowledge": knowledge_item,
    }


def extract_topics_from_text(text):
    found = []
    lower = str(text).lower()

    for key, topic in KEYWORD_TOPICS.items():
        if key in lower and topic not in found:
            found.append(topic)

    return found


def scan_context_topics():
    db = load_db()
    mem = load_memory()[-80:]

    texts = []

    for value in db.get("profile", {}).values():
        texts.append(str(value))

    for goal in db.get("goals", []):
        texts.append(str(goal))

    for project in db.get("projects", []):
        texts.append(str(project))

    for item in mem:
        texts.append(str(item))

    topics = []

    for text in texts:
        for topic in extract_topics_from_text(text):
            if topic not in topics:
                topics.append(topic)

    return topics


def curiosity_cycle():
    created = []

    for seed in SEED_TOPICS:
        result = add_topic(
            seed["topic"],
            reason=seed["reason"],
            priority=seed["priority"],
            source="seed",
        )
        if result.get("created"):
            created.append(result["item"])

    for topic in scan_context_topics():
        result = add_topic(
            topic,
            reason="detected from goals/projects/memory",
            priority=4,
            source="context_scan",
        )
        if result.get("created"):
            created.append(result["item"])

    queue = load_queue()
    knowledge = load_knowledge()

    return {
        "new_topics": created,
        "queue_size": len(queue),
        "open": len([x for x in queue if x.get("status") == "open"]),
        "learned": len(knowledge),
    }


def knowledge_status():
    queue = load_queue()
    knowledge = load_knowledge()

    return {
        "topics": len(queue) + len(knowledge),
        "open": len([x for x in queue if x.get("status") == "open"]),
        "queued": len(queue),
        "learned": len(knowledge),
        "top_open": sorted(
            [x for x in queue if x.get("status") == "open"],
            key=lambda x: x.get("priority", 5)
        )[:8],
    }


def active_learning_topics(limit=5):
    curiosity_cycle()
    queue = load_queue()
    open_items = sorted(
        [x for x in queue if x.get("status") == "open"],
        key=lambda x: x.get("priority", 5)
    )
    return [x.get("topic") for x in open_items[:limit]]
