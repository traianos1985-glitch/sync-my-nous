"""Authenticated chat transport: ordered tool events and one final response."""
import json
import queue
import threading

from flask import Response


def stream_execution(run):
    events = queue.Queue()
    cancelled = threading.Event()

    def emit(kind, data):
        if not cancelled.is_set():
            events.put((kind, data))

    def worker():
        try:
            emit("result", run(emit, cancelled.is_set))
        except Exception:
            emit("result", {"answer": "Η εκτέλεση διακόπηκε λόγω σφάλματος.", "mode": "degraded"})
        finally:
            events.put(None)

    def body():
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        try:
            while True:
                try:
                    item = events.get(timeout=10)
                except queue.Empty:
                    yield ": heartbeat\n\n"
                    continue
                if item is None:
                    break
                kind, data = item
                yield f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
        finally:
            cancelled.set()

    return Response(body(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})