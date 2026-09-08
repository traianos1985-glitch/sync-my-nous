import ast
import json
import os
import re
import time
from pathlib import Path

REPORT_FILE = "data/deep_code_analysis.json"

SCAN_DIRS = ["executor"]
MAX_FILE_BYTES = 200000


def _load():
    if not os.path.exists(REPORT_FILE):
        return []
    try:
        return json.load(open(REPORT_FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(REPORT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _read(path):
    try:
        p = Path(path)
        if not p.exists() or p.stat().st_size > MAX_FILE_BYTES:
            return ""
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _py_files():
    files = []
    for d in SCAN_DIRS:
        base = Path(d)
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if "__pycache__" not in str(p):
                files.append(str(p))
    return sorted(files)


def build_code_index():
    index = {
        "time": time.time(),
        "files": {},
        "routes": [],
        "functions": [],
        "imports": [],
    }

    for f in _py_files():
        text = _read(f)
        info = {
            "path": f,
            "size": len(text),
            "routes": [],
            "functions": [],
            "classes": [],
            "imports": [],
        }

        route_matches = re.findall(r'@app\.route\(["\']([^"\']+)["\'](?:,\s*methods=\[([^\]]+)\])?', text)
        for path, methods in route_matches:
            item = {
                "path": path,
                "methods": methods or "GET",
                "file": f,
            }
            info["routes"].append(item)
            index["routes"].append(item)

        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    item = {"name": node.name, "file": f, "line": node.lineno}
                    info["functions"].append(item)
                    index["functions"].append(item)
                elif isinstance(node, ast.ClassDef):
                    info["classes"].append({"name": node.name, "file": f, "line": node.lineno})
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    try:
                        src = ast.get_source_segment(text, node) or ""
                    except Exception:
                        src = ""
                    item = {"import": src, "file": f, "line": getattr(node, "lineno", None)}
                    info["imports"].append(item)
                    index["imports"].append(item)
        except Exception as e:
            info["parse_error"] = str(e)

        index["files"][f] = info

    return index


def _snippets_for_file(path, keywords):
    text = _read(path)
    if not text:
        return []

    lines = text.splitlines()
    snippets = []

    for i, line in enumerate(lines):
        low = line.lower()
        if any(k.lower() in low for k in keywords):
            start = max(0, i - 4)
            end = min(len(lines), i + 8)
            snippets.append({
                "file": path,
                "line": i + 1,
                "keyword_line": line,
                "snippet": "\n".join(f"{n+1}: {lines[n]}" for n in range(start, end)),
            })

    return snippets[:10]


def analyze_failure(problem):
    problem_text = json.dumps(problem, ensure_ascii=False).lower()
    index = build_code_index()

    keywords = []
    candidate_files = set()
    probable_area = "unknown"
    root_cause = "unknown"

    if "401" in problem_text or "unauthorized" in problem_text or "token" in problem_text:
        keywords += ["check_admin_token", "TOKEN", "authorization", "X-NOUS-Token", "unauthorized"]
        candidate_files.update(["executor/security.py", "executor/router.py", "executor/nous_ui.py"])
        probable_area = "auth"
        root_cause = "Authentication/token handling issue"

    if "404" in problem_text or "not found" in problem_text:
        keywords += ["@app.route", "route", "showSection", "fetch"]
        candidate_files.update(["executor/router.py", "executor/nous_ui.py"])
        probable_area = "routing"
        root_cause = "Missing or mismatched route"

    if "dashboard" in problem_text or "button" in problem_text or "onclick" in problem_text:
        keywords += ["onclick", "postJson", "getJson", "showSection", "fetch"]
        candidate_files.update(["executor/nous_ui.py", "executor/router.py"])
        probable_area = "dashboard"
        root_cause = "Dashboard frontend/backend action mismatch"

    if "mission-planner" in problem_text or "proposal" in problem_text:
        keywords += ["mission-planner", "propose_mission_for_goal", "approve_mission_proposal", "proposal_id"]
        candidate_files.update(["executor/mission_planner.py", "executor/router.py", "executor/nous_ui.py"])
        probable_area = "mission_planner"
        root_cause = "Mission planner flow issue"

    if "compile_error" in problem_text or "syntaxerror" in problem_text:
        probable_area = "compile"
        root_cause = "Python syntax/compile error"

    if not candidate_files:
        candidate_files.update(["executor/router.py", "executor/nous_ui.py"])
        keywords += ["error", "route", "postJson", "getJson"]

    snippets = []
    for f in sorted(candidate_files):
        snippets.extend(_snippets_for_file(f, keywords))

    matched_routes = []
    for r in index.get("routes", []):
        if r["path"].lower() in problem_text or any(part and part in problem_text for part in r["path"].lower().split("/") if len(part) > 3):
            matched_routes.append(r)

    report = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "problem": problem,
        "root_cause": root_cause,
        "probable_area": probable_area,
        "candidate_files": sorted(candidate_files),
        "keywords": sorted(set(keywords)),
        "matched_routes": matched_routes,
        "snippets": snippets[:20],
        "confidence": 0.82 if snippets or matched_routes else 0.45,
        "next_step": "Generate patch proposal. Do not apply without approval.",
    }

    items = _load()
    items.append(report)
    _save(items)

    return {"ok": True, "report": report}


def analyze_latest_diagnosis_deep():
    try:
        from executor.self_diagnosis import self_diagnosis_status
        st = self_diagnosis_status()
        problem = st.get("report", st)
    except Exception as e:
        problem = {"error": str(e)}
    return analyze_failure(problem)


def deep_code_analyst_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "recent": items[-10:],
    }


def list_deep_code_reports(limit=20):
    return _load()[-int(limit):]
