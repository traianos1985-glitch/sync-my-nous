"""Machine-readable catalog of built-in NOUS command tools."""
from __future__ import annotations


class _DependsOnRuntimeApproval:
    pass


DependsOnRuntimeApproval = _DependsOnRuntimeApproval()


TOOLS = (
    {
        "name": "calculate",
        "category": "utility",
        "description": "Evaluate arithmetic and approved math functions without Python eval.",
        "command": "calculate 12 * (4 + 3)",
        "risk": "local_computation",
        "approval_required": False,
    },
    {
        "name": "convert",
        "category": "utility",
        "description": "Convert length, mass, volume, speed, and temperature units.",
        "command": "convert 12 km to miles",
        "risk": "local_computation",
        "approval_required": False,
    },
    {
        "name": "time",
        "category": "utility",
        "description": "Return local time, UTC, or time in an IANA timezone.",
        "command": "time Europe/Athens",
        "risk": "read_only",
        "approval_required": False,
    },
    {
        "name": "text_stats",
        "category": "text",
        "description": "Count characters, non-whitespace characters, words, lines, and paragraphs.",
        "command": "text stats <text>",
        "risk": "local_computation",
        "approval_required": False,
    },
    {
        "name": "json_validate",
        "category": "data",
        "description": "Validate JSON and report the top-level type or parse location.",
        "command": "json validate <json>",
        "risk": "local_computation",
        "approval_required": False,
    },
    {
        "name": "sha256",
        "category": "data",
        "description": "Calculate a SHA-256 checksum of supplied UTF-8 text.",
        "command": "sha256 <text>",
        "risk": "local_computation",
        "approval_required": False,
    },
    {
        "name": "web_search",
        "category": "research",
        "description": "Search the web and return result titles and URLs.",
        "command": "search <query>",
        "risk": "external_read",
        "approval_required": False,
    },
    {
        "name": "fetch_page",
        "category": "research",
        "description": "Fetch and extract readable text from a URL.",
        "command": "open url https://example.com",
        "risk": "external_read",
        "approval_required": False,
    },
    {
        "name": "memory",
        "category": "memory",
        "description": "Read the most recent NOUS memory entries.",
        "command": "memory",
        "risk": "read_only",
        "approval_required": False,
    },
    {
        "name": "remember_fact",
        "category": "memory",
        "description": "Save a fact into NOUS personal memory.",
        "command": "remember <fact>",
        "risk": "state_change",
        "approval_required": False,
    },
    {
        "name": "plan",
        "category": "planning",
        "description": "Create a plan from a goal or request.",
        "command": "plan <goal>",
        "risk": "state_change",
        "approval_required": False,
    },
    {
        "name": "agent_solve",
        "category": "agent",
        "description": "Ask the agent executor to work on a goal.",
        "command": "agent solve <goal>",
        "risk": "agent_execution",
        "approval_required": DependsOnRuntimeApproval,
    },
)


def tool_catalog(category: str | None = None) -> dict:
    normalized = str(category or "").strip().lower()
    items = [dict(item) for item in TOOLS if not normalized or item["category"] == normalized]
    for item in items:
        if item.get("approval_required") is DependsOnRuntimeApproval:
            item["approval_required"] = "depends_on_action"
    return {
        "ok": True,
        "count": len(items),
        "categories": sorted({item["category"] for item in TOOLS}),
        "tools": items,
    }


def get_tool(name: str) -> dict | None:
    for item in TOOLS:
        if item["name"] == name:
            result = dict(item)
            if result.get("approval_required") is DependsOnRuntimeApproval:
                result["approval_required"] = "depends_on_action"
            return result
    return None
