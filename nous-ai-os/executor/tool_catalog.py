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
    {"name": "plugin", "category": "plugins", "description": "List installed plugins.", "command": "plugins", "risk": "read_only", "approval_required": False},
    {"name": "memory", "category": "memory", "description": "Read recent stored memory entries.", "command": "memory", "risk": "read_only", "approval_required": False},
    {"name": "memory_summary", "category": "memory", "description": "Summarize stored memory.", "command": "memory summary", "risk": "read_only", "approval_required": False},
    {"name": "remember_fact", "category": "memory", "description": "Save a fact in personal memory.", "command": "remember <fact>", "risk": "state_change", "approval_required": False},
    {"name": "recall", "category": "memory", "description": "Search remembered facts.", "command": "recall <query>", "risk": "read_only", "approval_required": False},
    {"name": "plan", "category": "planning", "description": "Create a plan from a goal.", "command": "plan <goal>", "risk": "state_change", "approval_required": False},
    {"name": "task", "category": "planning", "description": "Add a task.", "command": "task <description>", "risk": "state_change", "approval_required": False},
    {"name": "tasks", "category": "planning", "description": "List saved tasks.", "command": "tasks", "risk": "read_only", "approval_required": False},
    {"name": "web_search", "category": "research", "description": "Search the web.", "command": "search <query>", "risk": "external_read", "approval_required": False},
    {"name": "fetch_page", "category": "research", "description": "Extract text from a URL.", "command": "open url https://example.com", "risk": "external_read", "approval_required": False},
    {"name": "sysinfo", "category": "system", "description": "Read runtime information.", "command": "sysinfo", "risk": "read_only", "approval_required": False},
    {"name": "snapshot", "category": "system", "description": "Create a project snapshot report.", "command": "snapshot", "risk": "read_only", "approval_required": False},
    {"name": "compile", "category": "development", "description": "Run the code compile check.", "command": "compile", "risk": "read_only", "approval_required": False},
    {"name": "git_status", "category": "development", "description": "Inspect Git status.", "command": "git status", "risk": "read_only", "approval_required": False},
    {"name": "daily_brief", "category": "system", "description": "Generate the daily brief.", "command": "daily brief", "risk": "read_only", "approval_required": False},
    {"name": "agent_solve", "category": "agent", "description": "Ask the agent executor to work on a goal.", "command": "agent solve <goal>", "risk": "agent_execution", "approval_required": "depends_on_action"},
    {"name": "plan_goal", "category": "planning", "description": "Plan work for a goal.", "command": "plan goal <goal>", "risk": "state_change", "approval_required": False},
    {"name": "add_goal", "category": "planning", "description": "Create a personal goal.", "command": "goal <description>", "risk": "state_change", "approval_required": False},
    {"name": "add_project", "category": "planning", "description": "Register a project.", "command": "project <description>", "risk": "state_change", "approval_required": False},
    {"name": "personal_state", "category": "memory", "description": "Show personal state and goals.", "command": "profile", "risk": "read_only", "approval_required": False},
    {"name": "think_deep", "category": "reasoning", "description": "Run deeper reasoning on a question.", "command": "think <question>", "risk": "llm_request", "approval_required": False},
    {"name": "solve_problem", "category": "reasoning", "description": "Work through a problem.", "command": "solve <problem>", "risk": "llm_request", "approval_required": False},
    {"name": "decide", "category": "reasoning", "description": "Compare options and produce a decision.", "command": "decide <question>", "risk": "llm_request", "approval_required": False},
    {"name": "read_source", "category": "development", "description": "Read a project source file.", "command": "read source <relative-path>", "risk": "read_only", "approval_required": False},
    {"name": "stable", "category": "development", "description": "Create a stable checkpoint.", "command": "stable", "risk": "state_change", "approval_required": False},
    {"name": "git_checkpoint", "category": "development", "description": "Create a Git checkpoint.", "command": "git checkpoint <message>", "risk": "state_change", "approval_required": False},
    {"name": "make_plugin", "category": "plugins", "description": "Generate and test a plugin proposal.", "command": "make plugin <goal>", "risk": "code_generation", "approval_required": True},
    {"name": "forge_plugin", "category": "plugins", "description": "Generate a plugin through the code forge.", "command": "forge plugin <goal>", "risk": "code_generation", "approval_required": True},
    {"name": "run_plugin", "category": "plugins", "description": "Run an installed plugin.", "command": "run plugin <name>", "risk": "plugin_execution", "approval_required": True},
    {"name": "test_plugin", "category": "plugins", "description": "Test an installed plugin.", "command": "test plugin <name>", "risk": "plugin_execution", "approval_required": True},
    {"name": "quarantine_plugin", "category": "plugins", "description": "Move a plugin into quarantine.", "command": "quarantine plugin <name>", "risk": "state_change", "approval_required": True},
    {"name": "make_app", "category": "development", "description": "Generate a small web app.", "command": "make app <name>", "risk": "code_generation", "approval_required": True},
    {"name": "list_apps", "category": "development", "description": "List generated apps.", "command": "apps", "risk": "read_only", "approval_required": False},
    {"name": "agent_checkpoint", "category": "agent", "description": "Work on a goal and save a checkpoint.", "command": "agent checkpoint <goal>", "risk": "agent_execution", "approval_required": True},
    {"name": "agent_review", "category": "agent", "description": "Review the latest agent run.", "command": "agent review", "risk": "read_only", "approval_required": False},
    {"name": "team_plan", "category": "agent", "description": "Ask the agent team to plan a goal.", "command": "team plan <goal>", "risk": "agent_execution", "approval_required": True},
    {"name": "team_solve", "category": "agent", "description": "Ask the agent team to work on a goal.", "command": "team solve <goal>", "risk": "agent_execution", "approval_required": True},
    {"name": "schedule_task", "category": "automation", "description": "Add a scheduled task.", "command": "schedule <description>", "risk": "state_change", "approval_required": False},
    {"name": "clear_schedules", "category": "automation", "description": "Clear scheduled tasks.", "command": "clear schedules", "risk": "state_change", "approval_required": True},
    {"name": "sense", "category": "android", "description": "Read available Android sensor context.", "command": "sense", "risk": "read_only", "approval_required": False},
    {"name": "sense_think", "category": "android", "description": "Interpret Android sensor context.", "command": "sense think", "risk": "llm_request", "approval_required": False},
    {"name": "notify", "category": "android", "description": "Send a local NOUS notification.", "command": "notification", "risk": "side_effect", "approval_required": True},
    {"name": "next_action", "category": "planning", "description": "Suggest the next project action.", "command": "next action", "risk": "read_only", "approval_required": False},
    {"name": "action_log", "category": "system", "description": "Read recent action history.", "command": "actions", "risk": "read_only", "approval_required": False},
    {"name": "autonomy_start", "category": "automation", "description": "Start autonomous cycles.", "command": "autonomy start", "risk": "automation", "approval_required": True},
    {"name": "autonomy_stop", "category": "automation", "description": "Stop autonomous cycles.", "command": "autonomy stop", "risk": "state_change", "approval_required": False},
    {"name": "autonomy_status", "category": "automation", "description": "Inspect autonomy state.", "command": "autonomy status", "risk": "read_only", "approval_required": False},
    {"name": "autonomy_cycle", "category": "automation", "description": "Run one autonomy cycle.", "command": "autonomy cycle", "risk": "automation", "approval_required": True},
    {"name": "repair_system", "category": "system", "description": "Run system repair checks.", "command": "repair system", "risk": "state_change", "approval_required": True},
    {"name": "repair_advice", "category": "system", "description": "Generate repair advice.", "command": "repair advice", "risk": "read_only", "approval_required": False},

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
