import json
import os
import time

from executor.agent_journal import write_journal

BRIDGE_FILE = "data/remote_browser_jobs.json"


def _load():
    if not os.path.exists(BRIDGE_FILE):
        return []
    try:
        return json.load(open(BRIDGE_FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(BRIDGE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def create_browser_job(url, actions=None, reason="remote browser required"):
    items = _load()
    job = {
        "id": int(time.time_ns()),
        "url": url,
        "actions": actions or [],
        "reason": reason,
        "status": "pending_remote_worker",
        "created": time.time(),
        "result": None,
    }
    items.append(job)
    _save(items)
    write_journal("remote_browser_job_created", job)
    return job


def list_browser_jobs():
    return _load()


def complete_browser_job(job_id, result):
    items = _load()
    for job in items:
        if str(job.get("id")) == str(job_id):
            job["status"] = "done"
            job["result"] = result
            job["completed"] = time.time()
            _save(items)
            write_journal("remote_browser_job_completed", job)
            return job
    return {"ok": False, "error": "job_not_found"}


def remote_browser_bridge_status():
    jobs = _load()
    return {
        "mode": "remote_worker_queue",
        "pending": len([j for j in jobs if j.get("status") == "pending_remote_worker"]),
        "done": len([j for j in jobs if j.get("status") == "done"]),
        "jobs": jobs[-20:],
        "time": time.time(),
    }
