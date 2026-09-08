import json
import os
import time

from executor.executive_intelligence import executive_intelligence_status, executive_intelligence_report
from executor.brain_state import save_brain_state
from executor.decision_memory import record_decision
from executor.learning_memory import record_lesson

FILE = "data/executive_reviews.json"


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def run_executive_review(trigger="manual"):
    status = executive_intelligence_status()
    report = executive_intelligence_report()

    brain = save_brain_state()
    next_action = status.get("next_best_action", {})

    review = {
        "id": int(time.time_ns()),
        "time": time.time(),
        "trigger": trigger,
        "summary": status.get("summary", {}),
        "next_best_action": next_action,
        "recommendations": status.get("recommendations", []),
        "report": report.get("report"),
        "brain_readiness": brain.get("readiness", {}),
    }

    items = _load()
    items.append(review)
    _save(items)

    record_decision(
        title="Executive review: " + str(next_action.get("title", "No action")),
        reason=str(next_action.get("reason", "Scheduled executive review.")),
        action="executive_review",
        result={
            "trigger": trigger,
            "next_best_action": next_action,
            "summary": status.get("summary", {}),
        },
        confidence=0.75,
        tags=["executive_review", "scheduler", str(next_action.get("type", "unknown"))],
    )

    record_lesson(
        lesson="Executive review identified next best action: " + str(next_action.get("title", "No action")),
        outcome="success",
        confidence=0.7,
        tags=["executive_review", "scheduler", str(next_action.get("type", "unknown"))],
    )

    return {
        "ok": True,
        "review": review,
        "count": len(items),
    }


def list_executive_reviews(limit=20):
    return _load()[-int(limit):]


def executive_scheduler_status():
    reviews = _load()
    last = reviews[-1] if reviews else None

    return {
        "time": time.time(),
        "mode": "safe_review_only",
        "total_reviews": len(reviews),
        "last_review": last,
        "does_not_auto_execute": [
            "approvals",
            "deployments",
            "android_taps",
            "destructive_actions",
        ],
    }
