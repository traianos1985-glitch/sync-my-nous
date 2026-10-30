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
}


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
    raise ValueError("tool_not_allowed")


def execute_call(name, arguments, summary="", *, allow_web=True, on_event=None):
    record = {"id": str(uuid.uuid4()), "name": str(name)[:80], "input": arguments,
              "summary": str(summary)[:300], "status": "running", "started_at": time.time(), "executed": False}
    try:
        schema = SCHEMAS.get(name)
        if schema is None or (not allow_web and name in {"search_web", "search_wikipedia"}):
            raise ValueError("tool_not_allowed")
        if not isinstance(arguments, dict) or set(arguments) != set(schema):
            raise ValueError("invalid_tool_arguments")
        if any(not isinstance(arguments[k], t) or not arguments[k].strip() or len(arguments[k]) > 1000 for k, t in schema.items()):
            raise ValueError("invalid_tool_arguments")
        if on_event:
            on_event("tool", dict(record))
        result = dispatch(name, arguments)
        if isinstance(result, str) and result.startswith("[ERROR]"):
            raise RuntimeError("tool_execution_failed")
        if isinstance(result, dict) and (result.get("ok") is False or result.get("error")):
            raise RuntimeError("tool_execution_failed")
        encoded = json.dumps(result, ensure_ascii=False, default=str)
        record.update(status="completed", executed=True, output=result if len(encoded) <= 12000 else encoded[:12000] + "…")
    except ValueError as exc:
        record.update(status="blocked", error=str(exc))
    except Exception:
        record.update(status="failed", error="tool_execution_failed")
    record["finished_at"] = time.time()
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