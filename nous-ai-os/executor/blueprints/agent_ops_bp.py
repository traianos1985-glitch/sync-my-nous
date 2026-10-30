"""Agent Operations Blueprint: ReAct Loop, Swarm, Vector Memory, Self-Healing & Watchdog."""
from flask import Blueprint, jsonify, request
from executor.react_agent import run_react_task, GLOBAL_TOOL_REGISTRY
from executor.swarm_orchestrator import run_swarm
from executor.vector_memory import (
    store_vector_memory,
    search_vector_memory,
    get_vector_stats
)
from executor.self_healing_coder import self_heal_snippet
from executor.background_watchdog import run_watchdog_check
from executor.security import check_admin_token
from executor.url_reader_engine import summarize_url

agent_ops_bp = Blueprint("agent_ops_bp", __name__, url_prefix="/api/ops")


def _admin_required():
    """Keep operational endpoints behind the explicit admin boundary."""
    if not check_admin_token(request):
        return jsonify({"success": False, "error": "unauthorized"}), 401
    return None


@agent_ops_bp.route("/react/run", methods=["POST"])
def api_react_run():
    denied = _admin_required()
    if denied:
        return denied
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "json_object_required"}), 400
    task = data.get("task", "")
    if not isinstance(task, str) or not task.strip():
        return jsonify({"success": False, "error": "task is required"}), 400
    max_steps = data.get("max_steps", 5)
    if isinstance(max_steps, bool) or not isinstance(max_steps, int) or not 1 <= max_steps <= 5:
        return jsonify({"success": False, "error": "max_steps must be an integer from 1 to 5"}), 400
    res = run_react_task(task.strip(), max_steps=max_steps)
    return jsonify({"success": True, "result": res})


@agent_ops_bp.route("/research/read-url", methods=["POST"])
def api_research_read_url():
    """Read a public HTTP(S) page through the bounded, redirect-blocking URL reader."""
    denied = _admin_required()
    if denied:
        return denied
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "json_object_required"}), 400
    url = data.get("url")
    if not isinstance(url, str) or not url.strip() or len(url) > 2048:
        return jsonify({"success": False, "error": "valid_url_required"}), 400
    result = summarize_url(url.strip())
    return jsonify({"success": bool(result.get("ok")), "result": result}), (200 if result.get("ok") else 400)


@agent_ops_bp.route("/tools", methods=["GET"])
def api_tools_list():
    tools = GLOBAL_TOOL_REGISTRY.list_tools()
    return jsonify({"success": True, "tools": tools})


@agent_ops_bp.route("/tool-stats", methods=["GET"])
def api_tool_stats():
    """Read-only effectiveness statistics for the chat tool allowlist."""
    from executor.tool_telemetry import tool_stats
    return jsonify({"success": True, **tool_stats()})


@agent_ops_bp.route("/swarm/run", methods=["POST"])
def api_swarm_run():
    denied = _admin_required()
    if denied:
        return denied
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "json_object_required"}), 400
    mission = data.get("mission", data.get("task", ""))
    if not isinstance(mission, str) or not mission.strip():
        return jsonify({"success": False, "error": "mission is required"}), 400
    res = run_swarm(mission.strip(), data.get("context"))
    return jsonify({"success": True, "result": res})


@agent_ops_bp.route("/memory/vector/add", methods=["POST"])
def api_vector_add():
    denied = _admin_required()
    if denied:
        return denied
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "json_object_required"}), 400
    text = data.get("text", "")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"success": False, "error": "text is required"}), 400
    row_id = store_vector_memory(text, data.get("metadata"))
    return jsonify({"success": True, "id": row_id})


@agent_ops_bp.route("/memory/vector/search", methods=["GET", "POST"])
def api_vector_search():
    denied = _admin_required()
    if denied:
        return denied
    if request.method == "POST":
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "json_object_required"}), 400
        q = data.get("query", "")
        top_k = data.get("top_k", 5)
    else:
        q = request.args.get("q", "")
        top_k = request.args.get("top_k", "5")
    if not isinstance(q, str) or not q.strip():
        return jsonify({"success": False, "error": "query is required"}), 400
    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "invalid_top_k"}), 400
    if not 1 <= top_k <= 20:
        return jsonify({"success": False, "error": "invalid_top_k"}), 400
    hits = search_vector_memory(q.strip(), top_k=top_k)
    return jsonify({"success": True, "query": q.strip(), "results": hits})


@agent_ops_bp.route("/memory/vector/stats", methods=["GET"])
def api_vector_stats():
    denied = _admin_required()
    if denied:
        return denied
    stats = get_vector_stats()
    return jsonify({"success": True, "stats": stats})


@agent_ops_bp.route("/self-heal/run", methods=["POST"])
def api_self_heal():
    denied = _admin_required()
    if denied:
        return denied
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "json_object_required"}), 400
    filename = data.get("filename", "scratch.py")
    code = data.get("code", "")
    if not isinstance(filename, str) or not isinstance(code, str) or not code.strip():
        return jsonify({"success": False, "error": "valid filename and code are required"}), 400
    # Never accept a caller-supplied command. The public API only validates/heals
    # the supplied snippet; arbitrary subprocess execution is not exposed here.
    res = self_heal_snippet(filename, code)
    return jsonify({"success": True, "result": res})


@agent_ops_bp.route("/watchdog/run", methods=["POST", "GET"])
def api_watchdog_run():
    denied = _admin_required()
    if denied:
        return denied
    res = run_watchdog_check()
    return jsonify({"success": True, "report": res})
