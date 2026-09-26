from flask import Blueprint, jsonify
import time

system_bp = Blueprint("system_bp", __name__, url_prefix="/api/system")

@system_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "runtime": "NOUS-AI-OS",
        "version": "v4"
    })

@system_bp.route("/overview", methods=["GET"])
def overview():
    from executor.runtime_metrics import collect_metrics
    from executor.local_llm_adapter import local_llm_status
    return jsonify({
        "metrics": collect_metrics(),
        "local_llm": local_llm_status(),
        "timestamp": time.time()
    })
