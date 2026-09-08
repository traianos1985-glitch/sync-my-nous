import ast, json, os, time
from pathlib import Path

FILE = "data/repository_graph.json"

def build_repository_graph():
    graph = {"time": time.time(), "files": {}, "routes": [], "imports": [], "functions": []}

    for p in Path("executor").rglob("*.py"):
        if "__pycache__" in str(p):
            continue

        text = p.read_text(encoding="utf-8", errors="replace")
        info = {"path": str(p), "imports": [], "functions": [], "routes": []}

        try:
            tree = ast.parse(text)
            for n in ast.walk(tree):
                if isinstance(n, ast.FunctionDef):
                    item = {"file": str(p), "name": n.name, "line": n.lineno}
                    info["functions"].append(item)
                    graph["functions"].append(item)

                if isinstance(n, (ast.Import, ast.ImportFrom)):
                    item = {"file": str(p), "line": getattr(n, "lineno", None), "module": getattr(n, "module", None)}
                    info["imports"].append(item)
                    graph["imports"].append(item)
        except Exception as e:
            info["parse_error"] = str(e)

        for line_no, line in enumerate(text.splitlines(), start=1):
            if "@app.route" in line:
                item = {"file": str(p), "line": line_no, "route_line": line.strip()}
                info["routes"].append(item)
                graph["routes"].append(item)

        graph["files"][str(p)] = info

    os.makedirs("data", exist_ok=True)
    json.dump(graph, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return {"ok": True, "graph": graph}

def repository_graph_status():
    if not os.path.exists(FILE):
        return {"time": time.time(), "exists": False}
    data = json.load(open(FILE, "r", encoding="utf-8"))
    return {
        "time": time.time(),
        "exists": True,
        "files": len(data.get("files", {})),
        "routes": len(data.get("routes", [])),
        "functions": len(data.get("functions", [])),
        "imports": len(data.get("imports", [])),
        "graph": data,
    }
