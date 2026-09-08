"""NOUS Autonomous App Builder — human-in-the-loop."""
from __future__ import annotations

import ast
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

QUEUE = Path("data/app_builder_queue.json")
APPS_DIR = Path("apps")
REGISTRY = "data/apps.json"
APP_DIR = "generated_apps"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_queue() -> list:
    if not QUEUE.exists():
        return []
    try:
        return json.loads(QUEUE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_queue(q: list) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")


def _plan_id() -> str:
    return f"app_{int(time.time() * 1000)}"


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r"(\{[\s\S]*\})", text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return None


def plan_app(description: str) -> dict[str, Any]:
    """Ask LLM to plan + generate full app code. Returns plan with status=pending_approval."""
    from executor.remote_llm import ask_remote_llm

    prompt = f"""You are an expert Python software engineer building apps for the NOUS AI OS platform.

User request: {description}

Generate a complete, working implementation. Return ONLY valid JSON — no other text, no markdown outside the JSON:

{{
  "app_name": "snake_case_name",
  "title": "Human readable title in Greek",
  "description": "Τι κάνει αυτή η εφαρμογή",
  "tech_stack": ["Python", "Flask"],
  "files": [
    {{
      "path": "app_name/main.py",
      "description": "Short description",
      "content": "# full working code here"
    }},
    {{
      "path": "app_name/requirements.txt",
      "description": "Dependencies",
      "content": "flask\\nrequests"
    }}
  ],
  "run_command": "python apps/app_name/main.py",
  "install_notes": "pip install -r apps/app_name/requirements.txt",
  "notes": "Usage notes in Greek"
}}

Important rules:
- ALL file content must be complete and working — no placeholders, no TODO comments
- Path must start with app_name/ (files will be saved under apps/)
- For web apps use Flask on port 7000
- For scripts use pure Python with no external dependencies if possible
- Include requirements.txt only if external packages are needed (not stdlib)
- Code must be clean, readable, production-quality
"""

    result = ask_remote_llm(prompt)
    if not result.get("success"):
        return {"ok": False, "error": "LLM απέτυχε: " + str(result.get("error", "unknown"))}

    raw = result.get("response", "")
    plan_data = _extract_json(raw)

    if not plan_data or not plan_data.get("files"):
        app_slug = re.sub(r"[^a-z0-9_]", "_", description.lower()[:30]).strip("_") or "my_app"
        plan_data = {
            "app_name": app_slug,
            "title": description[:60],
            "description": description,
            "tech_stack": ["Python"],
            "files": [{"path": f"{app_slug}/main.py", "description": "Main", "content": raw}],
            "run_command": f"python apps/{app_slug}/main.py",
            "install_notes": "",
            "notes": "",
        }

    plan_id = _plan_id()
    plan = {
        "plan_id": plan_id,
        "status": "pending_approval",
        "created_at": now_iso(),
        "description": description,
        "app_name": plan_data.get("app_name", "my_app"),
        "title": plan_data.get("title", description[:60]),
        "tech_stack": plan_data.get("tech_stack", []),
        "files": plan_data.get("files", []),
        "run_command": plan_data.get("run_command", ""),
        "install_notes": plan_data.get("install_notes", ""),
        "notes": plan_data.get("notes", ""),
        "approved_at": None,
        "written_files": [],
        "build_result": None,
    }

    q = load_queue()
    q.append(plan)
    save_queue(q)

    return {"ok": True, "plan": plan}


def _syntax_check(path: Path) -> dict:
    if path.suffix not in {".py"}:
        return {"ok": True, "skipped": True}
    try:
        src = path.read_text(encoding="utf-8")
        ast.parse(src)
        return {"ok": True}
    except SyntaxError as e:
        return {"ok": False, "error": str(e), "line": e.lineno}


def approve_and_write(plan_id: str) -> dict[str, Any]:
    """Write all files for an approved plan."""
    q = load_queue()
    plan = next((p for p in q if p.get("plan_id") == plan_id), None)
    if not plan:
        return {"ok": False, "error": "Το plan δεν βρέθηκε"}
    if plan.get("status") == "approved":
        return {"ok": False, "error": "Έχει ήδη εγκριθεί"}

    APPS_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    errors = []

    for file_spec in plan.get("files", []):
        rel_path = str(file_spec.get("path", "")).strip().lstrip("/")
        content = str(file_spec.get("content", ""))
        if not rel_path or not content.strip():
            continue
        target = APPS_DIR / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(str(target))
        if target.suffix == ".py":
            chk = _syntax_check(target)
            if not chk.get("ok") and not chk.get("skipped"):
                errors.append({"file": str(target), "error": chk.get("error")})

    plan["status"] = "approved"
    plan["approved_at"] = now_iso()
    plan["written_files"] = written
    plan["build_result"] = {
        "files_written": len(written),
        "syntax_errors": errors,
        "ok": len(errors) == 0,
    }

    for i, p in enumerate(q):
        if p.get("plan_id") == plan_id:
            q[i] = plan
            break
    save_queue(q)

    return {
        "ok": True,
        "plan_id": plan_id,
        "app_name": plan.get("app_name"),
        "title": plan.get("title"),
        "files_written": written,
        "syntax_errors": errors,
        "run_command": plan.get("run_command"),
        "install_notes": plan.get("install_notes"),
        "location": str(APPS_DIR / plan.get("app_name", "")),
        "build_ok": len(errors) == 0,
    }


def reject_plan(plan_id: str) -> dict:
    q = load_queue()
    for i, p in enumerate(q):
        if p.get("plan_id") == plan_id:
            q[i]["status"] = "rejected"
            q[i]["rejected_at"] = now_iso()
            save_queue(q)
            return {"ok": True, "rejected": plan_id}
    return {"ok": False, "error": "plan_not_found"}


def list_builds() -> list:
    return load_queue()


def get_build(plan_id: str) -> dict | None:
    return next((p for p in load_queue() if p.get("plan_id") == plan_id), None)


# ── Legacy compatibility ──────────────────────────────────────────────────────

def _load():
    try:
        return json.load(open(REGISTRY, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(data):
    os.makedirs("data", exist_ok=True)
    json.dump(data, open(REGISTRY, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def list_apps():
    return _load()


def make_web_app(name, title=None, body=None):
    safe = "".join(c for c in name if c.isalnum() or c in "-_") or f"app_{int(time.time())}"
    title = title or safe
    body = body or "Web app generated by ΝΟΥΣ AI OS"
    path = os.path.join(APP_DIR, safe)
    os.makedirs(path, exist_ok=True)
    html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title><style>body{{font-family:Arial;background:#111;color:white;padding:20px}}
.card{{background:#1e1e1e;border-radius:16px;padding:20px}}
button{{padding:12px;border:0;border-radius:10px;background:#00ff88}}</style></head>
<body><div class="card"><h1>{title}</h1><p>{body}</p>
<button onclick="alert('ΝΟΥΣ app active')">OK</button></div></body></html>"""
    open(os.path.join(path, "index.html"), "w", encoding="utf-8").write(html)
    apps = _load()
    apps = [a for a in apps if a.get("name") != safe]
    apps.append({"name": safe, "title": title, "path": path, "url": f"/apps/{safe}/", "created": int(time.time())})
    _save(apps)
    return {"created": True, "name": safe, "path": path, "url": f"/apps/{safe}/"}


def status() -> dict:
    q = load_queue()
    pending = [p for p in q if p.get("status") == "pending_approval"]
    approved = [p for p in q if p.get("status") == "approved"]
    return {
        "tool": "App Builder",
        "total": len(q),
        "pending_approval": len(pending),
        "approved": len(approved),
        "pending": [{"plan_id": p["plan_id"], "title": p.get("title"), "created_at": p.get("created_at")} for p in pending],
    }
