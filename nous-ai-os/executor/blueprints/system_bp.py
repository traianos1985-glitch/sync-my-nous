from flask import Blueprint, jsonify
import os
import shutil
import time

system_bp = Blueprint("system_bp", __name__, url_prefix="/api/system")
STARTED_AT = time.time()


@system_bp.route("/health", methods=["GET"])
def health():
    # Liveness only: the process is responding, not a claim that every subsystem is healthy.
    return jsonify({
        "status": "healthy",
        "kind": "liveness",
        "timestamp": time.time(),
        "uptime_s": round(time.time() - STARTED_AT, 1),
        "runtime": "NOUS-AI-OS",
        "version": os.environ.get("NOUS_VERSION", "v4"),
    })


@system_bp.route("/ready", methods=["GET"])
def readiness():
    from executor.runtime_diagnostics import collect_diagnostics

    report = collect_diagnostics()
    return jsonify(report), (200 if report["ok"] else 503)


@system_bp.route("/diagnostics", methods=["GET"])
def diagnostics():
    from executor.runtime_diagnostics import collect_diagnostics

    return jsonify(collect_diagnostics())


@system_bp.route("/metrics", methods=["GET"])
def metrics():
    disk = shutil.disk_usage(".")
    data = {"uptime_s": round(time.time() - STARTED_AT, 1),
            "disk_free_mb": disk.free // 2**20, "timestamp": time.time()}
    try:
        import psutil
        data["cpu_percent"] = psutil.cpu_percent(interval=None)
        data["memory_percent"] = psutil.virtual_memory().percent
    except Exception:
        pass
    return jsonify(data)


@system_bp.route("/overview", methods=["GET"])
def overview():
    out = {"timestamp": time.time()}
    try:
        from executor.runtime_metrics import collect_metrics
        out["metrics"] = collect_metrics()
    except Exception as exc:
        out["metrics_error"] = f"{type(exc).__name__}: {str(exc)[:240]}"
    try:
        from executor.local_llm_adapter import local_llm_status
        out["local_llm"] = local_llm_status()
    except Exception as exc:
        out["local_llm_error"] = f"{type(exc).__name__}: {str(exc)[:240]}"
    return jsonify(out), (200 if "metrics" in out else 503)
