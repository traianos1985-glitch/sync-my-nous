"""Real, bounded mission actions beyond static health checks (audit N-05).

Every action here is read-only toward the host (web search, guarded page reads,
memory search, static code analysis, isolated app tests, a read-only ReAct step).
Payloads are validated up front so a mission plan never stores an action it cannot
run, and results are trimmed to JSON-safe summaries so mission evidence stays small
and never carries raw page markup or private model reasoning.
"""
from __future__ import annotations

import ast
import os
import math
import re
import time
from pathlib import Path
from typing import Any, Callable

MAX_QUERY_CHARS = 500
MAX_GOAL_CHARS = 2000
MAX_TEXT_EXCERPT = 4000
MAX_ANALYSIS_FILES = 400
_APP_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")
_REPO_ROOT = Path(__file__).resolve().parent.parent

# action -> {field: (type, required)}
PAYLOAD_SCHEMAS: dict[str, dict[str, tuple[type, bool]]] = {
    "search_web": {"query": (str, True), "max_results": (int, False)},
    "read_url": {"url": (str, True), "limit": (int, False)},
    "search_memory": {"query": (str, True), "limit": (int, False)},
    "knowledge_search": {"query": (str, True), "limit": (int, False), "content_type": (str, False)},
    "code_analysis": {"path": (str, False)},
    "app_validation": {"app_name": (str, True), "timeout_seconds": (int, False)},
    "agent_task": {"goal": (str, True), "max_steps": (int, False), "allow_web": (bool, False)},
    "github_read": {"owner": (str, True), "repo": (str, True), "path": (str, False), "branch": (str, False), "query": (str, False)},
    "github_commit": {"owner": (str, True), "repo": (str, True), "path": (str, True), "content": (str, True),
                      "message": (str, True), "branch": (str, False)},
    "github_deploy_pages": {"app_name": (str, True), "repo_name": (str, False), "dry_run": (bool, False)},
    "larmor_calculate": {"material": (str, True), "b_field_tesla": (float, True)},
    "field_log": {"title": (str, True), "note": (str, False), "lat": (float, False), "lon": (float, False)},
}

# Actions that change external state: mission_system requires explicit operator approval.
APPROVAL_ACTIONS = frozenset({"github_commit", "github_deploy_pages"})
# Read-only actions retried once on a transient failure.
RETRYABLE_ACTIONS = frozenset({"search_web", "read_url", "github_read"})
MAX_COMMIT_CHARS = 200_000

MISSION_ACTIONS = frozenset(PAYLOAD_SCHEMAS)
# Read-only actions the unattended auto-mission executor may also run.
AUTO_SAFE_ACTIONS = frozenset({"search_web", "read_url", "search_memory", "knowledge_search", "code_analysis",
                               "github_read", "larmor_calculate"})


class MissionPayloadError(ValueError):
    pass


def validate_payload(action: str, payload: Any) -> dict[str, Any]:
    schema = PAYLOAD_SCHEMAS.get(action)
    if schema is None:
        raise MissionPayloadError("unknown_mission_action")
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise MissionPayloadError("payload_must_be_object")
    unknown = set(payload) - set(schema)
    if unknown:
        raise MissionPayloadError("unexpected_payload_field")
    for field, (kind, required) in schema.items():
        if field not in payload:
            if required:
                raise MissionPayloadError(f"missing_{field}")
            continue
        value = payload[field]
        if kind is int and (isinstance(value, bool) or not isinstance(value, int)):
            raise MissionPayloadError(f"invalid_{field}")
        if kind is float:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise MissionPayloadError(f"invalid_{field}")
            continue
        if kind is not int and not isinstance(value, kind):
            raise MissionPayloadError(f"invalid_{field}")
        if kind is str:
            limit = (MAX_GOAL_CHARS if field in {"goal", "note"} else 2048 if field == "url"
                     else MAX_COMMIT_CHARS if field == "content" else MAX_QUERY_CHARS)
            if (required and not value.strip()) or len(value) > limit:
                raise MissionPayloadError(f"invalid_{field}")
    if action == "app_validation" and not _APP_SLUG.fullmatch(payload["app_name"]):
        raise MissionPayloadError("invalid_app_name")
    if action == "github_deploy_pages" and not _APP_SLUG.fullmatch(payload["app_name"]):
        raise MissionPayloadError("invalid_app_name")
    if action == "larmor_calculate" and payload["b_field_tesla"] <= 0:
        raise MissionPayloadError("invalid_b_field_tesla")
    if action == "field_log":
        if ("lat" in payload) != ("lon" in payload):
            raise MissionPayloadError("coordinates_must_be_paired")
        if "lat" in payload and not (-90 <= payload["lat"] <= 90 and -180 <= payload["lon"] <= 180):
            raise MissionPayloadError("invalid_coordinates")
    return payload


def _bounded(value: Any, default: int, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    return max(low, min(value, high))


def _excerpt(text: Any, limit: int = 600) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


# ------------------------------------------------------------------ web research

def action_search_web(payload: dict[str, Any]) -> dict[str, Any]:
    from executor import web_search

    query = payload["query"].strip()
    max_results = _bounded(payload.get("max_results"), 5, 1, 10)
    result = web_search.search(query, max_results=max_results)
    if not result.get("ok"):
        return {"ok": False, "error": str(result.get("error") or "search_failed"), "query": query}
    items = [
        {"title": _excerpt(item.get("title"), 200), "url": str(item.get("url", ""))[:500],
         "snippet": _excerpt(item.get("snippet"), 400)}
        for item in result.get("results", []) if isinstance(item, dict)
    ]
    if not items:
        return {"ok": False, "error": "no_results", "query": query}
    return {"ok": True, "query": query, "count": len(items), "results": items, "source": "web_search"}


def action_read_url(payload: dict[str, Any]) -> dict[str, Any]:
    from executor.research_broker import validate_url
    from executor.url_reader_engine import read_url

    url = payload["url"].strip()
    try:
        safe_url = validate_url(url)
    except ValueError as exc:
        return {"ok": False, "error": f"unsafe_url:{exc}", "url": url[:500]}
    limit = _bounded(payload.get("limit"), MAX_TEXT_EXCERPT, 200, 12000)
    page = read_url(safe_url, limit=limit)
    if not isinstance(page, dict) or not page.get("ok"):
        error = page.get("error") if isinstance(page, dict) else "malformed_reader_result"
        return {"ok": False, "error": str(error or "read_failed"), "url": safe_url}
    text = str(page.get("text") or page.get("content") or "")
    if not text.strip():
        return {"ok": False, "error": "empty_page", "url": safe_url}
    return {
        "ok": True,
        "url": safe_url,
        "title": _excerpt(page.get("title"), 300),
        "text": text[:limit],
        "chars": len(text),
        "source": "url_reader_engine",
    }


# ------------------------------------------------------------------ memory / knowledge

def action_search_memory(payload: dict[str, Any]) -> dict[str, Any]:
    from executor.knowledge_memory_engine import search_knowledge

    query = payload["query"].strip()
    limit = _bounded(payload.get("limit"), 5, 1, 20)
    found = search_knowledge(query, limit=limit)
    hits = found.get("hits", []) if isinstance(found, dict) else []
    items = [
        {"id": str(hit.get("id")), "question": _excerpt(hit.get("question"), 300),
         "answer": _excerpt(hit.get("answer"), 800), "score": hit.get("score"),
         "kind": hit.get("kind"), "sources": [str(s)[:300] for s in (hit.get("sources") or [])][:5],
         "provenance": hit.get("provenance") if isinstance(hit.get("provenance"), dict) else None}
        for hit in hits if isinstance(hit, dict)
    ]
    # An empty result is a truthful completed search, not a failure.
    return {"ok": True, "query": query, "count": len(items), "hits": items, "source": "knowledge_memory"}


def action_knowledge_search(payload: dict[str, Any]) -> dict[str, Any]:
    from executor.knowledge_panel import search_documents

    query = payload["query"].strip()
    limit = _bounded(payload.get("limit"), 5, 1, 20)
    documents = search_documents(query, content_type=str(payload.get("content_type", "")), limit=limit)
    memory = action_search_memory({"query": query, "limit": limit})
    docs = [
        {"id": d.get("id"), "document": d.get("documentName"), "score": d.get("score"),
         "excerpt": _excerpt(d.get("text"), 600)}
        for d in documents if isinstance(d, dict)
    ]
    return {"ok": True, "query": query, "documents": docs, "memory_hits": memory.get("hits", []),
            "count": len(docs) + memory.get("count", 0), "source": "knowledge_base"}


# ------------------------------------------------------------------ code analysis

def _resolve_analysis_root(raw: str | None) -> Path:
    root = _REPO_ROOT
    target = (root / (raw or "executor")).resolve()
    if target != root and root not in target.parents:
        raise MissionPayloadError("path_outside_repository")
    if any(part.startswith(".") for part in target.relative_to(root).parts):
        raise MissionPayloadError("private_path_blocked")
    if not target.exists():
        raise MissionPayloadError("path_not_found")
    return target


def action_code_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    """Static AST quality scan: syntax errors, long functions, bare excepts, TODOs."""
    try:
        target = _resolve_analysis_root(payload.get("path"))
    except MissionPayloadError as exc:
        return {"ok": False, "error": str(exc)}
    files = [target] if target.is_file() else sorted(
        p for p in target.rglob("*.py")
        if not any(part in {"__pycache__", "node_modules", ".venv", "venv"} or part.startswith(".")
                   for part in p.relative_to(target).parts)
    )
    truncated = len(files) > MAX_ANALYSIS_FILES
    files = files[:MAX_ANALYSIS_FILES]
    syntax_issues, long_functions = [], []
    totals = {"files": 0, "lines": 0, "functions": 0, "classes": 0, "bare_excepts": 0, "todo_markers": 0}
    for path in files:
        rel = str(path.relative_to(_REPO_ROOT))
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            syntax_issues.append({"file": rel, "issue": "unreadable"})
            continue
        totals["files"] += 1
        totals["lines"] += source.count("\n") + 1
        totals["todo_markers"] += len(re.findall(r"#\s*(?:TODO|FIXME|XXX)\b", source))
        try:
            tree = ast.parse(source, filename=rel)
        except SyntaxError as exc:
            syntax_issues.append({"file": rel, "issue": "syntax", "line": exc.lineno})
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                totals["functions"] += 1
                length = (getattr(node, "end_lineno", node.lineno) or node.lineno) - node.lineno + 1
                if length > 120:
                    long_functions.append({"file": rel, "function": node.name, "lines": length})
            elif isinstance(node, ast.ClassDef):
                totals["classes"] += 1
            elif isinstance(node, ast.ExceptHandler) and node.type is None:
                totals["bare_excepts"] += 1
    long_functions.sort(key=lambda item: item["lines"], reverse=True)
    score = 100 - min(60, len(syntax_issues) * 20) - min(25, len(long_functions)) - min(15, totals["bare_excepts"])
    return {
        "ok": not syntax_issues,
        "target": str(target.relative_to(_REPO_ROOT)) or ".",
        "totals": totals,
        "quality_score": max(0, score),
        "syntax_issues": syntax_issues[:50],
        "long_functions": long_functions[:20],
        "files_truncated": truncated,
        **({"error": "syntax_errors_found"} if syntax_issues else {}),
    }


# ------------------------------------------------------------------ app validation

def action_app_validation(payload: dict[str, Any]) -> dict[str, Any]:
    from executor.app_validation_runner import run_project_tests

    apps_root = Path(os.environ.get("NOUS_GENERATED_APPS_DIR", "data/generated_apps"))
    if not (apps_root / payload["app_name"]).is_dir():
        from executor.app_builder import APPS_DIR
        apps_root = Path(APPS_DIR)
    timeout = _bounded(payload.get("timeout_seconds"), 120, 5, 300)
    result = run_project_tests(payload["app_name"], apps_root, timeout_seconds=timeout)
    if not isinstance(result, dict):
        return {"ok": False, "error": "malformed_validation_result"}
    keep = ("ok", "status", "error", "return_code", "duration_seconds", "stdout", "stderr", "isolation")
    return {key: result[key] for key in keep if key in result} | {"app_name": payload["app_name"]}


# ------------------------------------------------------------------ agent reasoning step

_FALLBACK_ANSWERS = ("Το AI δεν είναι διαθέσιμο",)


def action_agent_task(payload: dict[str, Any], planner: Callable | None = None) -> dict[str, Any]:
    from executor.react_agent import run_chat_react

    if planner is None:
        from executor.remote_llm import ask_with_turns as planner  # type: ignore[assignment]
    planner_ok = {"value": False}

    def tracked(turns, system=None):
        result = planner(turns, system=system)
        if isinstance(result, dict) and result.get("success"):
            planner_ok["value"] = True
        return result

    result = run_chat_react(
        [{"role": "user", "content": payload["goal"].strip()}],
        tracked,
        max_steps=_bounded(payload.get("max_steps"), 3, 1, 3),
        allow_web=bool(payload.get("allow_web", True)),
    )
    calls = [
        {"tool": c.get("name"), "outcome": c.get("status"), "summary": _excerpt(c.get("summary"), 200)}
        for c in result.get("tool_calls", []) if isinstance(c, dict)
    ]
    completed = [c for c in calls if c["outcome"] == "completed"]
    answer = str(result.get("answer") or "")
    real_answer = planner_ok["value"] and answer and not answer.startswith(_FALLBACK_ANSWERS)
    if not completed and not real_answer:
        return {"ok": False, "error": "agent_step_produced_no_result", "steps": calls}
    return {"ok": True, "answer": answer[:MAX_TEXT_EXCERPT], "steps": calls,
            "tools_completed": len(completed), "source": "react_agent"}


HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "search_web": action_search_web,
    "read_url": action_read_url,
    "search_memory": action_search_memory,
    "knowledge_search": action_knowledge_search,
    "code_analysis": action_code_analysis,
    "app_validation": action_app_validation,
    "agent_task": action_agent_task,
}


def action_github_read(payload: dict[str, Any]) -> dict[str, Any]:
    from executor import github_operator as gh
    owner, repo = payload["owner"], payload["repo"]
    if "query" in payload:
        return gh.search_code(owner, repo, payload["query"])
    path = payload.get("path", "")
    if path in {"", "/", ".pages"}:
        if path == ".pages":
            return gh.get_pages_status(owner, repo)
        return gh.get_repository_tree(owner, repo, "", payload.get("branch"))
    result = gh.get_file_content(owner, repo, path, payload.get("branch"))
    if result.get("error") == "not_a_file":
        return gh.get_repository_tree(owner, repo, path, payload.get("branch"))
    if result.get("ok") and isinstance(result.get("content"), str):
        result["content"] = result["content"][:MAX_TEXT_EXCERPT * 5]
    return result


def action_github_commit(payload: dict[str, Any]) -> dict[str, Any]:
    from executor import github_operator as gh
    existing = gh.get_file_content(payload["owner"], payload["repo"], payload["path"], payload.get("branch"))
    sha = existing.get("sha") if existing.get("ok") else None
    result = gh.commit_file(payload["owner"], payload["repo"], payload["path"], payload["content"],
                            payload["message"], payload.get("branch"), sha)
    if result.get("ok"):
        # Closed-loop verification: read the file back and compare with what was committed.
        check = gh.get_file_content(payload["owner"], payload["repo"], payload["path"], payload.get("branch"))
        result["verified"] = bool(check.get("ok")) and check.get("content") == payload["content"]
        if not result["verified"]:
            return {**result, "ok": False, "error": "commit_verification_failed"}
    return result


def action_github_deploy_pages(payload: dict[str, Any]) -> dict[str, Any]:
    from executor import github_operator as gh
    result = gh.deploy_sandbox_app_to_github(payload["app_name"], payload.get("repo_name"), None,
                                             dry_run=payload.get("dry_run", False))
    if result.get("ok") and not result.get("dry_run") and result.get("owner") and result.get("repo_name"):
        result["pages_check"] = gh.get_pages_status(result["owner"], result["repo_name"])
    return result


def action_larmor_calculate(payload: dict[str, Any]) -> dict[str, Any]:
    from executor.larmor_bridge import calculate_larmor
    result = calculate_larmor(payload["material"], float(payload["b_field_tesla"]))
    if not isinstance(result, dict) or result.get("error"):
        error = str((result or {}).get("error") or "larmor_failed")
        return {"ok": False, "error": "unknown_material" if error.startswith("Unknown material") else "larmor_invalid_input",
                "detail": error[:200]}
    return {"ok": True, "result": result, "note": "Θεωρητικός υπολογισμός αναφοράς, όχι μέτρηση ανίχνευσης."}


def action_field_log(payload: dict[str, Any]) -> dict[str, Any]:
    from executor.field_engine import add_entry, get_entry
    result = add_entry(payload["title"], payload.get("note", ""), payload.get("lat"), payload.get("lon"),
                       entry_type="note", tags=["nous", "unverified"])
    entry = (result or {}).get("entry") or {}
    # Closed-loop verification: the saved entry must be readable again.
    if not result.get("ok") or not entry.get("id") or not get_entry(entry["id"]):
        return {"ok": False, "error": "field_log_verification_failed"}
    return {"ok": True, "entry": entry, "verified": True}


HANDLERS.update({
    "github_read": action_github_read,
    "github_commit": action_github_commit,
    "github_deploy_pages": action_github_deploy_pages,
    "larmor_calculate": action_larmor_calculate,
    "field_log": action_field_log,
})


def run_mission_action(action: str, payload: Any) -> dict[str, Any]:
    started = time.time()
    try:
        clean = validate_payload(action, payload)
    except MissionPayloadError as exc:
        err_res = {"ok": False, "error": str(exc), "action": action}
        try:
            from executor.failure_memory import record_failure
            record_failure("mission_actions", action, str(exc), {"error_type": "payload_validation"})
        except Exception:
            pass
        return err_res
    try:
        from executor.failure_memory import known_blocking_failure
        known = known_blocking_failure("mission_actions", action)
    except Exception:
        known = None
    if known:
        return {"ok": False, "error": "known_failure_avoided", "action": action, "previous_error": known.get("error"),
                "suggested_fix": known.get("suggested_fix"), "duration_ms": 0.0}
    try:
        result = HANDLERS[action](clean)
        if action in RETRYABLE_ACTIONS and isinstance(result, dict) and not result.get("ok") \
                and str(result.get("error")) not in _persistent_errors():
            result = HANDLERS[action](clean)
            if isinstance(result, dict):
                result["retried"] = True
    except Exception as exc:  # exception text may embed URLs/paths; keep only the type
        result = {"ok": False, "error": "mission_action_exception", "detail": type(exc).__name__}
        try:
            from executor.failure_memory import record_failure
            record_failure("mission_actions", action, type(exc).__name__, {"detail": "handler_exception"})
        except Exception:
            pass
    if not isinstance(result, dict):
        result = {"ok": False, "error": "malformed_action_result"}
    elif not result.get("ok"):
        try:
            from executor.failure_memory import record_failure
            error = str(result.get("error") or "action_failed")
            record_failure(
                "mission_actions",
                action,
                error,
                {"detail": str(result.get("detail") or "")},
                suggested_fix=_SUGGESTED_FIXES.get(error),
            )
        except Exception:
            pass
    result["duration_ms"] = round((time.time() - started) * 1000, 1)
    return result


_SUGGESTED_FIXES = {
    "missing_token": "Πρόσθεσε GitHub token στις ρυθμίσεις του NOUS",
    "github_http_401": "Το GitHub token έληξε ή είναι λάθος",
    "github_http_403": "Το GitHub token δεν έχει τα απαιτούμενα δικαιώματα",
    "github_http_404": "Έλεγξε owner/repo/path",
    "unknown_material": "Δες τη λίστα υλικών στο Larmor Studio",
}


def _persistent_errors() -> frozenset:
    try:
        from executor.failure_memory import PERSISTENT_ERRORS
        return PERSISTENT_ERRORS
    except Exception:
        return frozenset()
