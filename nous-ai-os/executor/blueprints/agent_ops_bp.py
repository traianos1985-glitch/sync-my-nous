"""Agent Operations Blueprint: ReAct Loop, Swarm & Vector Memory Endpoints."""
from flask import Blueprint, jsonify, request
from executor.react_agent import run_react_task, GLOBAL_TOOL_REGISTRY
from executor.swarm_orchestrator import run_swarm
from executor.vector_memory import (
    store_vector_memory,
    search_vector_memory,
    get_vector_stats
)

agent_ops_bp = Blueprint("agent_ops_bp", __name__, url_prefix="/api/ops")

@agent_ops_bp.route("/react/run", methods=["POST"])
def api_react_run():
    data = request.get_json(silent=True) or {}
    task = data.get("task", "")
    if not task:
        return jsonify({"success": False, "error": "task is required"}), 400
    res = run_react_task(task, max_steps=data.get("max_steps", 5))
    return jsonify({"success": True, "result": res})

@agent_ops_bp.route("/tools", methods=["GET"])
def api_tools_list():
    tools = GLOBAL_TOOL_REGISTRY.list_tools()
    return jsonify({"success": True, "tools": tools})

@agent_ops_bp.route("/swarm/run", methods=["POST"])
def api_swarm_run():
    data = request.get_json(silent=True) or {}
    mission = data.get("mission", data.get("task", ""))
    if not mission:
        return jsonify({"success": False, "error": "mission is required"}), 400
    res = run_swarm(mission, data.get("context"))
    return jsonify({"success": True, "result": res})

@agent_ops_bp.route("/memory/vector/add", methods=["POST"])
def api_vector_add():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"success": False, "error": "text is required"}), 400
    row_id = store_vector_memory(text, data.get("metadata"))
    return jsonify({"success": True, "id": row_id})

@agent_ops_bp.route("/memory/vector/search", methods=["GET", "POST"])
def api_vector_search():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        q = data.get("query", "")
        top_k = int(data.get("top_k", 5))
    else:
        q = request.args.get("q", "")
        top_k = int(request.args.get("top_k", 5))
        
    if not q:
        return jsonify({"success": False, "error": "query is required"}), 400
    hits = search_vector_memory(q, top_k=top_k)
    return jsonify({"success": True, "query": q, "results": hits})

@agent_ops_bp.route("/memory/vector/stats", methods=["GET"])
def api_vector_stats():
    stats = get_vector_stats()
    return jsonify({"success": True, "stats": stats})
