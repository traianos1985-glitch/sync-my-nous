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

from executor.engineering_standards import APPLICATION_ENGINEERING_GUIDE, validate_app_plan

QUEUE = Path("data/app_builder_queue.json")
APP_DIR = os.environ.get("NOUS_GENERATED_APPS_DIR", "data/generated_apps")
APPS_DIR = Path(APP_DIR)
REGISTRY = "data/apps.json"


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
    """Generate a structured, review-only application plan with engineering checks."""
    from executor.remote_llm import ask_remote_llm

    request = str(description or "").strip()
    if not request:
        return {"ok": False, "error": "empty_description"}
    if len(request) > 8000:
        return {"ok": False, "error": "description_too_long", "max_characters": 8000}

    prompt = f"""You are a senior software architect and engineer building complete applications for NOUS AI OS.

USER REQUIREMENT:
{request}

{APPLICATION_ENGINEERING_GUIDE}

Return ONLY valid JSON with this exact top-level shape:
{{
  "app_name": "snake_case_name",
  "title": "Human-readable title",
  "description": "Purpose and behavior",
  "tech_stack": ["Python", "Flask"],
  "files": [
    {{"path": "app_name/main.py", "description": "Application entry point", "content": "complete source"}},
    {{"path": "app_name/tests/test_main.py", "description": "Automated regression tests", "content": "complete tests"}},
    {{"path": "app_name/README.md", "description": "Setup and usage documentation", "content": "complete documentation"}}
  ],
  "run_command": "python main.py",
  "install_notes": "Reproducible setup instructions",
  "notes": "Assumptions and limitations"
}}

Hard requirements:
- Return all source, test, documentation, and configuration files needed; do not return only a mockup or calculator unless that is explicitly the requested scope.
- Every path must begin with the exact app_name plus '/'. Do not use absolute paths, '..', backslashes, or paths outside the application folder.
- Include a meaningful README.md, at least one automated test file under app_name/tests/, and a real entry point.
- Tests must cover core behavior and important invalid-input/failure cases; do not merely test that a constant exists.
- Web UI must provide real interactions and loading/empty/error states; never rely on alert() as the main UI.
- For web applications use the appropriate stack rather than defaulting blindly to Flask. Keep backend, domain logic, persistence, and UI separated when the scope warrants it.
- If a database is required, implement real persistence and safe initialization/migrations. Never claim an integration works when credentials or services are unavailable.
- Use environment configuration for secrets; include a placeholder-only .env.example when useful. Never include real secrets.
- Do not include TODOs, placeholders, fake endpoints, fabricated success, or markdown outside the JSON.
- Keep dependencies minimal. Include requirements.txt or package.json only when appropriate.
- Assume sensible defaults instead of asking follow-up questions; document important assumptions in notes.
"""

    result = ask_remote_llm(prompt)
    if not isinstance(result, dict) or not result.get("success"):
        error = result.get("error", "unknown") if isinstance(result, dict) else "invalid_llm_response"
        return {"ok": False, "error": "llm_generation_failed", "details": str(error)[:500]}

    raw = result.get("response", "")
    plan_data = _extract_json(raw)
    if not isinstance(plan_data, dict):
        return {
            "ok": False,
            "error": "invalid_app_plan_json",
            "details": "Το μοντέλο δεν επέστρεψε έγκυρο JSON. Δεν αποθηκεύτηκε σχέδιο.",
        }

    validation_errors = validate_app_plan(plan_data)
    if validation_errors:
        return {
            "ok": False,
            "error": "app_plan_validation_failed",
            "validation_errors": validation_errors,
            "retryable": True,
        }

    plan_id = _plan_id()
    plan = {
        "plan_id": plan_id,
        "status": "pending_approval",
        "created_at": now_iso(),
        "description": request,
        "app_name": plan_data["app_name"],
        "title": plan_data["title"].strip(),
        "tech_stack": plan_data.get("tech_stack", []),
        "files": plan_data["files"],
        "run_command": plan_data.get("run_command", ""),
        "install_notes": plan_data.get("install_notes", ""),
        "notes": plan_data.get("notes", ""),
        "approved_at": None,
        "written_files": [],
        "build_result": None,
        "engineering_validation": {
            "ok": True,
            "checks": ["schema", "safe_paths", "unique_paths", "readme", "automated_test_file", "entrypoint", "size_limits"],
            "runtime_tests_executed": False,
        },
    }

    q = load_queue()
    q.append(plan)
    save_queue(q)

    return {"ok": True, "plan": plan}

def _safe_app_target(rel_path: object, app_name: object) -> Path:
    """Resolve a generated file path and reject traversal and symlink escapes."""
    raw = str(rel_path or "").strip()
    slug = str(app_name or "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", slug):
        raise ValueError("invalid_app_name")
    if not raw or chr(92) in raw or chr(0) in raw:
        raise ValueError("invalid_path")
    if re.match(r"^[A-Za-z]:", raw):
        raise ValueError("absolute_path_not_allowed")
    parts = raw.split("/")
    if raw.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("path_traversal_not_allowed")
    if len(parts) < 2 or parts[0] != slug:
        raise ValueError("path_must_be_inside_app_directory")
    root = APPS_DIR.resolve()
    target = root.joinpath(*parts).resolve()
    if target == root or root not in target.parents:
        raise ValueError("path_outside_apps_directory")
    return target


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
    if plan.get("status") != "pending_approval":
        return {"ok": False, "error": "plan_not_pending"}

    APPS_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    errors = []
    prepared = []
    seen_targets = set()
    app_name = plan.get("app_name", "")

    # Validate every path before writing anything to prevent partial writes on bad plans.
    for file_spec in plan.get("files", []):
        if not isinstance(file_spec, dict):
            return {"ok": False, "error": "invalid_file_spec"}
        content = str(file_spec.get("content", ""))
        if not content.strip():
            continue
        try:
            target = _safe_app_target(file_spec.get("path"), app_name)
        except ValueError as exc:
            return {"ok": False, "error": "unsafe_app_path", "details": str(exc)}
        target_key = str(target)
        if target_key in seen_targets:
            return {"ok": False, "error": "duplicate_app_path", "path": str(file_spec.get("path", ""))}
        seen_targets.add(target_key)
        prepared.append((target, content))

    for target, content in prepared:
        target.parent.mkdir(parents=True, exist_ok=True)
        resolved_target = target.resolve()
        resolved_root = APPS_DIR.resolve()
        if resolved_target == resolved_root or resolved_root not in resolved_target.parents:
            return {"ok": False, "error": "path_outside_apps_directory", "path": str(target)}
        resolved_target.write_text(content, encoding="utf-8")
        written.append(str(resolved_target))
        if resolved_target.suffix == ".py":
            chk = _syntax_check(resolved_target)
            if not chk.get("ok") and not chk.get("skipped"):
                errors.append({"file": str(resolved_target), "error": chk.get("error")})

    entrypoints = {"main.py", "app.py", "run.py", "server.py"}
    entrypoint = next((target for target, _ in prepared if target.name in entrypoints), APPS_DIR / app_name / "main.py")
    plan["run_command"] = f"python {entrypoint}"
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
            if p.get("status") != "pending_approval":
                return {"ok": False, "error": "plan_not_pending"}
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
