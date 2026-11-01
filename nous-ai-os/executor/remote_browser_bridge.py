"""Remote browser job queue with atomic, locked persistence and local fallback (N-06).

Read-only research jobs (open/read a public URL, or a search query) are fulfilled
immediately on this host through ``url_reader_engine`` / ``web_search`` so they never
sit in ``pending_remote_worker``. Only interactive jobs (click/fill) wait for a real
remote worker, and the status reports honestly whether one has ever checked in.
"""
import json
import os
import tempfile
import time
from contextlib import contextmanager

from executor import portable_fcntl as fcntl
from executor.agent_journal import write_journal

BRIDGE_FILE = "data/remote_browser_jobs.json"
MAX_JOBS = 500


@contextmanager
def _locked():
    directory = os.path.dirname(BRIDGE_FILE) or "."
    os.makedirs(directory, exist_ok=True)
    with open(BRIDGE_FILE + ".lock", "a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _load():
    if not os.path.exists(BRIDGE_FILE):
        return []
    try:
        with open(BRIDGE_FILE, "r", encoding="utf-8") as handle:
            items = json.load(handle)
    except (OSError, ValueError):
        return []
    return items if isinstance(items, list) else []


def _save(items):
    directory = os.path.dirname(BRIDGE_FILE) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".remote_browser_jobs.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items[-MAX_JOBS:], handle, ensure_ascii=False, indent=2, default=str)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, BRIDGE_FILE)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _fulfil_locally(url, actions, query):
    from executor.browser_driver_operator import (
        INTERACTIVE_ACTIONS, fallback_read, fallback_search, guard_url,
    )

    types = [a.get("type") for a in actions if isinstance(a, dict)]
    if any(t in INTERACTIVE_ACTIONS for t in types):
        return None  # needs a real browser; leave for a remote worker
    if url:
        safe_url, reason = guard_url(url)
        if safe_url is None:
            return {"ok": False, "error": f"invalid_url:{reason}"}
        return fallback_read(safe_url)
    if query:
        return fallback_search(query)
    return {"ok": False, "error": "url_or_query_required"}


def create_browser_job(url, actions=None, reason="remote browser required", query=None):
    actions = actions if isinstance(actions, list) else []
    url = str(url or "").strip()
    query = str(query or "").strip()
    job = {
        "id": int(time.time_ns()),
        "url": url,
        "query": query or None,
        "actions": actions,
        "reason": str(reason)[:300],
        "status": "pending_remote_worker",
        "created": time.time(),
        "result": None,
    }
    local = _fulfil_locally(url, actions, query)
    if local is not None:
        job["status"] = "done" if local.get("ok") else "failed"
        job["result"] = local
        job["completed"] = time.time()
        job["fulfilled_by"] = "local_fallback"
    with _locked():
        items = _load()
        items.append(job)
        _save(items)
    write_journal("remote_browser_job_created", {k: v for k, v in job.items() if k != "result"})
    return job


def list_browser_jobs():
    return _load()


def complete_browser_job(job_id, result):
    with _locked():
        items = _load()
        for job in items:
            if str(job.get("id")) == str(job_id):
                if job.get("status") != "pending_remote_worker":
                    return {"ok": False, "error": "job_not_pending", "status": job.get("status")}
                job["status"] = "done"
                job["result"] = result
                job["completed"] = time.time()
                job["fulfilled_by"] = "remote_worker"
                _save(items)
                write_journal("remote_browser_job_completed", {"id": job["id"]})
                return job
    return {"ok": False, "error": "job_not_found"}


def remote_browser_bridge_status():
    jobs = _load()
    return {
        "mode": "remote_worker_queue_with_local_fallback",
        "pending": len([j for j in jobs if j.get("status") == "pending_remote_worker"]),
        "done": len([j for j in jobs if j.get("status") == "done"]),
        "failed": len([j for j in jobs if j.get("status") == "failed"]),
        "remote_worker_seen": any(j.get("fulfilled_by") == "remote_worker" for j in jobs),
        "jobs": jobs[-20:],
        "time": time.time(),
    }
