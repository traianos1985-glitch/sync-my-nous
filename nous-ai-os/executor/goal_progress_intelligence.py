import time

from executor.goal_system import list_goals
from executor.mission_system import list_missions
from executor.learning_memory import list_lessons
from executor.decision_memory import list_decisions


KEYWORDS = {
    "cloud": ["cloud", "backup", "restore", "brain", "vercel", "sync", "portable"],
    "ui": ["ui", "dashboard", "interface", "panel", "mobile", "button"],
    "android": ["android", "companion", "ui_tree", "tap", "back", "home"],
    "autonomy": ["autonomy", "executive", "scheduler", "approval", "recommendation", "mission", "lesson", "decision"],
}


def _text(obj):
    return str(obj).lower()


def _goal_category(goal):
    t = _text(goal)
    if "cloud" in t or "restorable" in t:
        return "cloud"
    if "interface" in t or "dashboard" in t or "user interface" in t:
        return "ui"
    if "android" in t or "companion" in t:
        return "android"
    if "autonomy" in t or "missions" in t or "approvals" in t:
        return "autonomy"
    return "autonomy"


def _score_for_category(category, missions, lessons, decisions):
    words = KEYWORDS.get(category, [])
    score = 0
    evidence = []

    for m in missions:
        mt = _text(m)
        if any(w in mt for w in words):
            if m.get("status") == "done":
                score += 25
                evidence.append({"type": "mission_done", "id": m.get("id"), "title": m.get("title")})
            elif m.get("status") == "active":
                score += 10
                evidence.append({"type": "mission_active", "id": m.get("id"), "title": m.get("title")})
            elif m.get("status") == "blocked":
                score += 5
                evidence.append({"type": "mission_blocked", "id": m.get("id"), "title": m.get("title")})

    for l in lessons:
        lt = _text(l)
        if any(w in lt for w in words):
            if l.get("outcome") == "success":
                score += 10
            else:
                score += 3
            evidence.append({"type": "lesson", "id": l.get("id"), "lesson": l.get("lesson")})

    for d in decisions:
        dt = _text(d)
        if any(w in dt for w in words):
            score += 5
            evidence.append({"type": "decision", "id": d.get("id"), "title": d.get("title")})

    
    category_caps = {
        "cloud": 70,
        "ui": 70,
        "android": 75,
        "autonomy": 80,
    }
    return min(score, category_caps.get(category, 75)), evidence[:20]



def analyze_goal_progress():
    goals = list_goals()
    missions = list_missions()
    lessons = list_lessons(500)
    decisions = list_decisions(500)

    results = []

    for g in goals:
        category = _goal_category(g)
        score, evidence = _score_for_category(category, missions, lessons, decisions)

        category_caps = {
            "cloud": 70,
            "ui": 70,
            "android": 75,
            "autonomy": 80,
        }
        score = min(score, category_caps.get(category, 75))

        current = int(g.get("progress", 0) or 0)
        recommended = score

        results.append({
            "goal_id": g.get("id"),
            "title": g.get("title"),
            "category": category,
            "current_progress": current,
            "recommended_progress": recommended,
            "delta": recommended - current,
            "evidence": evidence,
        })

    return {
        "time": time.time(),
        "results": results,
    }


def apply_goal_progress_intelligence():
    from executor.goal_system import _load, _save

    analysis = analyze_goal_progress()
    items = _load()
    by_id = {str(x["goal_id"]): x for x in analysis["results"]}

    changed = []

    for g in items:
        r = by_id.get(str(g.get("id")))
        if not r:
            continue

        old = int(g.get("progress", 0) or 0)
        new = int(r["recommended_progress"])

        if new != old:
            g["progress"] = new
            g["updated"] = time.time()
            g.setdefault("notes", []).append({
                "time": time.time(),
                "note": "Goal progress intelligence recalibrated progress from %s%% to %s%%." % (old, new),
                "evidence_count": len(r.get("evidence", [])),
            })
            changed.append({
                "goal_id": g.get("id"),
                "title": g.get("title"),
                "old": old,
                "new": new,
            })

        if g.get("progress", 0) >= 100:
            g["status"] = "done"

    _save(items)

    return {
        "ok": True,
        "changed": changed,
        "analysis": analysis,
        "time": time.time(),
    }


def goal_progress_intelligence_status():
    analysis = analyze_goal_progress()
    return {
        "time": time.time(),
        "goals": len(analysis.get("results", [])),
        "needs_update": [r for r in analysis.get("results", []) if r.get("delta", 0) > 0],
        "analysis": analysis,
    }
