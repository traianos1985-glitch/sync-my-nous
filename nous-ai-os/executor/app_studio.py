"""App Studio transport: bounded live validation and explicit repair decisions."""
from __future__ import annotations

import difflib
import json
import queue
import threading
from flask import Blueprint, Response, jsonify, request, stream_with_context
from executor.security import check_admin_token

studio_bp = Blueprint("app_studio", __name__, url_prefix="/remote/app-builder")
_repair_lock = threading.RLock()


@studio_bp.post("/test-stream")
def test_stream():
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("app_name"), str):
        return jsonify({"ok": False, "error": "invalid_request_body"}), 400
    try:
        timeout = int(data.get("timeout_seconds", 120))
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "invalid_timeout"}), 400
    if not 1 <= timeout <= 300:
        return jsonify({"ok": False, "error": "timeout_out_of_range"}), 400
    from executor.app_builder import APPS_DIR
    from executor.app_validation_runner import run_project_tests
    events = queue.Queue(maxsize=256)
    cancelled = threading.Event()

    def emit(kind, value):
        if cancelled.is_set():
            return
        try:
            events.put((kind, value), timeout=0.1)
        except queue.Full:
            pass

    def run():
        try:
            result = run_project_tests(data["app_name"], APPS_DIR, timeout,
                                       on_output=lambda text: emit("output", {"text": text}),
                                       cancelled=cancelled)
        except Exception:
            result = {"ok": False, "status": "error", "error": "runner_failed"}
        # Preserve the terminal event even when console updates saturated the queue.
        while not cancelled.is_set():
            try:
                events.put(("result", result), timeout=0.1)
                break
            except queue.Full:
                continue

    @stream_with_context
    def generate():
        threading.Thread(target=run, daemon=True).start()
        try:
            yield 'event: status\ndata: {"status":"running"}\n\n'
            while True:
                try:
                    kind, value = events.get(timeout=5)
                except queue.Empty:
                    yield ": keepalive\n\n"
                    continue
                yield f"event: {kind}\ndata: {json.dumps(value, ensure_ascii=False)}\n\n"
                if kind == "result":
                    break
        finally:
            cancelled.set()
    return Response(generate(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@studio_bp.get("/repairs")
def repairs():
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    from executor.app_repair_review import _read_store
    app_name = request.args.get("app", "")
    return jsonify({"ok": True, "repairs": [p for p in _read_store("data/app_builder_repairs.json") if p.get("app_name") == app_name]})


@studio_bp.get("/repair/<repair_id>")
def repair_detail(repair_id):
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    from executor.app_builder import APPS_DIR
    from executor.app_repair_review import _read_store, review_repair_proposal
    with _repair_lock:
        proposal = next((p for p in _read_store("data/app_builder_repairs.json") if p.get("repair_id") == repair_id), None)
        if proposal is None:
            return jsonify({"ok": False, "error": "repair_not_found"}), 404
        review = review_repair_proposal(repair_id, APPS_DIR)
        changes = []
        if review.get("ready_for_human_review"):
            for change in proposal["changes"]:
                target = APPS_DIR / change["path"]
                before = target.read_text(encoding="utf-8") if target.is_file() else ""
                changes.append({**change, "before": before, "diff": "".join(difflib.unified_diff(before.splitlines(True), change["content"].splitlines(True), fromfile=change["path"], tofile=change["path"]))})
        return jsonify({"ok": True, "proposal": proposal, "review": review, "changes": changes})


@studio_bp.post("/repair-approve")
def repair_approve():
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    from executor.app_builder import APPS_DIR
    from executor.app_repair_review import resolve_repair_proposal
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"ok": False, "error": "invalid_request_body"}), 400
    with _repair_lock:
        result = resolve_repair_proposal(data.get("repair_id"), APPS_DIR, approve=True)
    return jsonify(result), (200 if result.get("ok") else 409)


@studio_bp.post("/repair-reject")
def repair_reject():
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    from executor.app_builder import APPS_DIR
    from executor.app_repair_review import resolve_repair_proposal
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"ok": False, "error": "invalid_request_body"}), 400
    with _repair_lock:
        result = resolve_repair_proposal(data.get("repair_id"), APPS_DIR, approve=False)
    return jsonify(result), (200 if result.get("ok") else 409)