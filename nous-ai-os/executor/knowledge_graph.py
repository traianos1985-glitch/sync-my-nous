import json, os, time

FILE = "data/knowledge_graph.json"

def build_knowledge_graph():
    graph = {"time": time.time(), "nodes": [], "edges": []}

    def node(t, i, label, data=None):
        graph["nodes"].append({"type": t, "id": str(i), "label": label, "data": data or {}})

    def edge(a, b, rel):
        graph["edges"].append({"from": str(a), "to": str(b), "rel": rel})

    try:
        from executor.goal_system import list_goals
        for g in list_goals():
            gid = "goal:" + str(g.get("id"))
            node("goal", gid, g.get("title"), g)
    except Exception:
        pass

    try:
        from executor.goal_manager_v2 import list_goal_projects
        for p in list_goal_projects():
            pid = "project:" + str(p.get("id"))
            gid = "goal:" + str(p.get("goal_id"))
            node("project", pid, p.get("title"), p)
            edge(gid, pid, "has_project")
    except Exception:
        pass

    try:
        from executor.mission_system import mission_status
        for m in mission_status().get("missions", []):
            mid = "mission:" + str(m.get("id"))
            node("mission", mid, m.get("title"), m)
            for t in m.get("tasks", []):
                tid = "task:" + str(t.get("id"))
                node("task", tid, t.get("title"), t)
                edge(mid, tid, "has_task")
    except Exception:
        pass

    try:
        from executor.learning_memory import list_lessons
        for l in list_lessons(200):
            lid = "lesson:" + str(l.get("id"))
            node("lesson", lid, l.get("lesson"), l)
            if l.get("mission_id"):
                edge("mission:" + str(l.get("mission_id")), lid, "produced_lesson")
    except Exception:
        pass

    os.makedirs("data", exist_ok=True)
    json.dump(graph, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return {"ok": True, "graph": graph}

def knowledge_graph_status():
    if not os.path.exists(FILE):
        return {"time": time.time(), "exists": False}
    data = json.load(open(FILE, "r", encoding="utf-8"))
    return {
        "time": time.time(),
        "exists": True,
        "nodes": len(data.get("nodes", [])),
        "edges": len(data.get("edges", [])),
        "graph": data,
    }
