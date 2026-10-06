import json
import time
from flask import Blueprint, Response, request
from executor.agent_journal import list_journal

events_bp = Blueprint("events_sse", __name__, url_prefix="/api")

@events_bp.route("/agent/stream", methods=["GET"])
def agent_stream():
    """Server-Sent Events stream for real-time agent journal and feedback."""
    def generate():
        last_count = 0
        iterations = 0
        while iterations < 60:
            try:
                entries = list_journal()
                if len(entries) > last_count:
                    new_entries = entries[last_count:]
                    last_count = len(entries)
                    yield f"event: agent_journal\ndata: {json.dumps(new_entries)}\n\n"
                
                yield f"event: ping\ndata: {json.dumps({'time': time.time(), 'status': 'alive'})}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            time.sleep(2)
            iterations += 1

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive"
    })

@events_bp.route("/missions/stream", methods=["GET"])
def missions_stream():
    """Server-Sent Events stream for autonomous missions progress."""
    def generate():
        # list_missions lives in executor.mission_system (auto_mission_scheduler
        # does not export it) — importing it from the wrong module raised an
        # ImportError on the first chunk and turned the whole SSE stream into a 500.
        from executor.mission_system import list_missions
        for _ in range(30):
            try:
                missions = list_missions()
                yield f"event: missions_update\ndata: {json.dumps(missions)}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            time.sleep(3)

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive"
    })
