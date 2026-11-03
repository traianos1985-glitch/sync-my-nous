"""Narrow chat-only tool bindings. Catalog presence never grants execution rights."""
from __future__ import annotations

import json
import re
import time
import uuid

from executor.react_agent import GLOBAL_TOOL_REGISTRY, _resolve_workspace_path
from executor.tool_catalog import get_tool

SCHEMAS = {
    "system_status": {}, "missions_status": {}, "list_dir": {"path": str},
    "read_file": {"path": str}, "search_web": {"query": str},
    "search_memory": {"query": str}, "search_wikipedia": {"query": str},
    "calculate": {"expression": str},
    # GitHub Operator (read-only; writes become approval-gated missions).
    "github_status": {}, "github_list_repos": {},
    "github_read": {"owner": str, "repo": str, "path": str},
    "github_search": {"owner": str, "repo": str, "query": str},
    "github_pages_status": {"owner": str, "repo": str},
    "github_commit_request": {"owner": str, "repo": str, "path": str, "content": str, "message": str},
    # Larmor Engine and field diary.
    "larmor_calculate": {"material": str, "b_field_tesla": str},
    "field_log": {"title": str, "note": str},
}
LONG_FIELDS = {"content": 200_000}
WEB_TOOLS = {"search_web", "search_wikipedia"}


def _mission_action(action, payload):
    from executor.mission_actions import run_mission_action
    result = run_mission_action(action, payload)
    return result


def dispatch(name, arguments):
    if name == "system_status":
        from executor.tools import run_tool
        if get_tool("sysinfo").get("approval_required") is not False:
            raise ValueError("tool_not_allowed")
        return run_tool({"action": "sysinfo"}, {})
    if name == "calculate":
        from executor.tools import run_tool
        return run_tool({"action": "calculate"}, {"command": "calculate " + arguments["expression"]})
    if name == "missions_status":
        from executor.mission_system import list_missions
        return {"missions": [{"id": m.get("id"), "title": m.get("title"), "status": m.get("status")} for m in list_missions()[:100]]}
    if name in {"read_file", "list_dir"}:
        target = _resolve_workspace_path(arguments["path"])
        if any(part.startswith(".") and part != "." for part in target.relative_to(_resolve_workspace_path(".")).parts):
            raise ValueError("private_file_blocked")
        if re.search(r"(?:secret|credential|token|private.?key|\.pem$|\.key$)", target.name, re.I):
            raise ValueError("private_file_blocked")
        tool = GLOBAL_TOOL_REGISTRY.get(name)
        if tool is None:
            raise ValueError("tool_not_available")
        return tool(**arguments)
    if name == "search_web":
        from executor.browser_automation import browser_search
        return browser_search(arguments["query"])
    if name == "search_memory":
        from executor.knowledge_memory_engine import search_knowledge
        return {"hits": search_knowledge(arguments["query"], limit=3)}
    if name == "search_wikipedia":
        from executor.internet_search_engine import _wikipedia_search
        return {"results": _wikipedia_search(arguments["query"])[:3]}
    if name == "github_status":
        from executor.github_operator import get_github_status
        return get_github_status()
    if name == "github_list_repos":
        from executor.github_operator import list_repositories
        return list_repositories(per_page=30)
    if name == "github_read":
        path = arguments["path"].strip()
        return _mission_action("github_read", {"owner": arguments["owner"], "repo": arguments["repo"],
                                               **({} if path in {"/", "."} else {"path": path})})
    if name == "github_search":
        return _mission_action("github_read", {"owner": arguments["owner"], "repo": arguments["repo"],
                                               "query": arguments["query"]})
    if name == "github_pages_status":
        return _mission_action("github_read", {"owner": arguments["owner"], "repo": arguments["repo"], "path": ".pages"})
    if name == "larmor_calculate":
        try:
            tesla = float(arguments["b_field_tesla"].replace(",", "."))
        except ValueError:
            raise ValueError("invalid_tool_arguments")
        return _mission_action("larmor_calculate", {"material": arguments["material"].strip(), "b_field_tesla": tesla})
    if name == "field_log":
        return _mission_action("field_log", {"title": arguments["title"][:120], "note": arguments["note"]})
    if name == "github_commit_request":
        # Never commits from chat: creates a mission whose task waits for operator approval.
        from executor.mission_actions import validate_payload
        from executor.mission_system import create_mission
        payload = {k: arguments[k] for k in ("owner", "repo", "path", "content", "message")}
        validate_payload("github_commit", payload)
        mission = create_mission(f"GitHub commit: {payload['repo']}/{payload['path']}"[:120],
                                 payload["message"], [{"action": "github_commit", "payload": payload}])
        if not mission.get("ok", True) or not mission.get("id") and not (mission.get("mission") or {}).get("id"):
            return {"ok": False, "error": mission.get("error") or "mission_create_failed"}
        mid = mission.get("id") or mission["mission"]["id"]
        return {"ok": True, "mission_id": mid, "status": "waiting_approval", "committed": False,
                "message": "Η αλλαγή περιμένει έγκριση στις Εγκρίσεις πριν σταλεί στο GitHub."}
    raise ValueError("tool_not_allowed")


def execute_call(name, arguments, summary="", *, allow_web=True, on_event=None):
    record = {"id": str(uuid.uuid4()), "name": str(name)[:80], "input": arguments,
              "summary": str(summary)[:300], "status": "running", "started_at": time.time(), "executed": False}
    try:
        schema = SCHEMAS.get(name)
        if schema is None or (not allow_web and name in WEB_TOOLS):
            raise ValueError("tool_not_allowed")
        if not isinstance(arguments, dict) or set(arguments) != set(schema):
            raise ValueError("invalid_tool_arguments")
        if any(not isinstance(arguments[k], t) or not arguments[k].strip()
               or len(arguments[k]) > LONG_FIELDS.get(k, 1000) for k, t in schema.items()):
            raise ValueError("invalid_tool_arguments")
        from executor.failure_memory import known_blocking_failure
        known = known_blocking_failure("chat_tools", name)
        if known:
            raise ValueError("known_failure_avoided:" + str(known.get("error"))[:60])
        if on_event:
            on_event("tool", dict(record))
        result = dispatch(name, arguments)
        if isinstance(result, str) and result.startswith("[ERROR]"):
            raise RuntimeError("tool_execution_failed")
        if isinstance(result, dict) and (result.get("ok") is False or result.get("error")):
            record["error_detail"] = str(result.get("error") or "")[:80]
            raise RuntimeError("tool_execution_failed")
        encoded = json.dumps(result, ensure_ascii=False, default=str)
        record.update(status="completed", executed=True, output=result if len(encoded) <= 12000 else encoded[:12000] + "…")
    except ValueError as exc:
        record.update(status="blocked", error=str(exc))
    except Exception:
        record.update(status="failed", error="tool_execution_failed")
    record["finished_at"] = time.time()
    if record["status"] == "failed":
        try:
            from executor.failure_memory import record_failure
            record_failure("chat_tools", record["name"], record.get("error_detail") or "tool_execution_failed")
        except Exception:
            pass
    try:
        from executor import tool_telemetry
        tool_telemetry.record_outcome(
            record["name"], record["status"],
            (record["finished_at"] - record["started_at"]) * 1000.0,
            record.get("error"), known_names=SCHEMAS,
        )
    except Exception:
        pass  # telemetry is best-effort and must never alter tool execution
    if on_event:
        on_event("tool", dict(record))
    return record


def initial_call(message):
    """Only explicit read requests bypass existing conversational early returns."""
    text = message.strip()
    lower = text.lower()
    read = re.match(r"^(?:διάβασε|διαβασε|read(?: file)?)\s+(?:το αρχείο\s+)?[\"`']?([^\"`'\n]+)[\"`']?$", text, re.I)
    if read and not read.group(1).startswith(("https://", "http://")):
        return {"name": "read_file", "input": {"path": read.group(1).strip()}}
    if re.search(r"(?:system status|system health|έλεγξε.*σύστημα|ελεγξε.*συστημα|κατάσταση.*συστήματος|κατασταση.*συστηματος)", lower):
        return {"name": "system_status", "input": {}}
    if re.search(r"(?:missions? status|list missions|κατάσταση.*missions|κατάσταση.*αποστολ|δείξε.*missions|δείξε.*αποστολ)", lower):
        return {"name": "missions_status", "input": {}}
    search = re.match(r"^(?:ψάξε|ψαξε|αναζήτησε|αναζητησε|search)\s+(.+)$", text, re.I)
    if search:
        return {"name": "search_web", "input": {"query": search.group(1)}}
    return None