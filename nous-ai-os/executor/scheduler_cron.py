"""Safe scheduled NOUS jobs with bounded actions and durable state."""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

SCHEDULE_FILE = Path("data/scheduler_cron.json")
_scheduler_thread: threading.Thread | None = None
_running = False
_STATE_LOCK = threading.RLock()
_DAY_NAMES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
# Cron is intentionally limited to low-risk housekeeping. Destructive or
# developer-facing NOUS Drive proposals must never be auto-approved by a timer.
SCHEDULED_AUTO_APPROVE_ACTIONS = frozenset({
    "generate_morning_brief",
    "generate_evening_summary",
    "create_backup",
    "self_reflection",
})

DEFAULT_JOBS = [
    {"name": "Πρωινή Αναφορά", "action": "generate_morning_brief", "hour": 8, "minute": 0},
    {"name": "Βραδινή Αναφορά", "action": "generate_evening_summary", "hour": 21, "minute": 0},
    {"name": "Νυχτερινό Backup", "action": "create_backup", "hour": 2, "minute": 0},
    {"name": "Αυτο-αναστοχασμός", "action": "self_reflection", "hour": 12, "minute": 0},
]


def _default_state() -> dict[str, Any]:
    now = time.time()
    return {
        "jobs": [
            {
                "id": int(time.time_ns()) + index,
                "name": item["name"],
                "action": item["action"],
                "hour": item["hour"],
                "minute": item["minute"],
                "days": list(_DAY_NAMES),
                "enabled": True,
                "created": now,
                "last_run": None,
            }
            for index, item in enumerate(DEFAULT_JOBS)
        ],
        "log": [],
    }


def _load() -> dict[str, Any]:
    with _STATE_LOCK:
        if not SCHEDULE_FILE.exists():
            state = _default_state()
            _save(state)
            return state
        try:
            state = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("schedule_store_unavailable") from exc
        if (
            not isinstance(state, dict)
            or not isinstance(state.get("jobs"), list)
            or not isinstance(state.get("log", []), list)
            or any(not isinstance(job, dict) for job in state["jobs"])
        ):
            raise ValueError("schedule_store_invalid_structure")
        state.setdefault("log", [])
        for job in state["jobs"]:
            if not isinstance(job.get("action"), str) or job["action"] not in SCHEDULED_AUTO_APPROVE_ACTIONS:
                raise ValueError("schedule_store_invalid_job")
            hour, minute = job.get("hour"), job.get("minute", 0)
            if (
                isinstance(hour, bool) or not isinstance(hour, int) or not 0 <= hour <= 23
                or isinstance(minute, bool) or not isinstance(minute, int) or not 0 <= minute <= 59
            ):
                raise ValueError("schedule_store_invalid_job")
            if "enabled" in job and not isinstance(job["enabled"], bool):
                raise ValueError("schedule_store_invalid_job")
            days = job.get("days", list(_DAY_NAMES))
            if not isinstance(days, list) or not days or any(
                not isinstance(day, str) or day not in _DAY_NAMES for day in days
            ):
                raise ValueError("schedule_store_invalid_job")
        return state


def _save(state: dict[str, Any]) -> None:
    if not isinstance(state, dict) or not isinstance(state.get("jobs"), list):
        raise ValueError("schedule_store_invalid_structure")
    SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=SCHEDULE_FILE.parent,
            prefix=".scheduler-cron-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = handle.name
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, SCHEDULE_FILE)
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


def add_job(name: str, action: str, hour: int, minute: int = 0,
            days: list | None = None) -> dict:
    clean_name = str(name or "").strip()
    clean_action = str(action or "").strip()
    if not clean_name or len(clean_name) > 80:
        return {"ok": False, "error": "invalid_job_name"}
    if clean_action not in SCHEDULED_AUTO_APPROVE_ACTIONS:
        return {"ok": False, "error": "action_not_allowlisted"}
    if isinstance(hour, bool) or isinstance(minute, bool):
        return {"ok": False, "error": "invalid_schedule_time"}
    try:
        hour_value, minute_value = int(hour), int(minute)
    except (TypeError, ValueError, OverflowError):
        return {"ok": False, "error": "invalid_schedule_time"}
    if not 0 <= hour_value <= 23 or not 0 <= minute_value <= 59:
        return {"ok": False, "error": "invalid_schedule_time"}

    if days is None:
        day_values = list(_DAY_NAMES)
    elif isinstance(days, list) and days and all(isinstance(day, str) for day in days):
        day_values = list(dict.fromkeys(day.lower() for day in days))
        if not day_values or any(day not in _DAY_NAMES for day in day_values):
            return {"ok": False, "error": "invalid_schedule_days"}
    else:
        return {"ok": False, "error": "invalid_schedule_days"}

    with _STATE_LOCK:
        state = _load()
        if len(state["jobs"]) >= 50:
            return {"ok": False, "error": "schedule_limit_reached"}
        job = {
            "id": int(time.time_ns()),
            "name": clean_name,
            "action": clean_action,
            "hour": hour_value,
            "minute": minute_value,
            "days": day_values,
            "enabled": True,
            "created": time.time(),
            "last_run": None,
        }
        state["jobs"].append(job)
        _save(state)
        return job


def list_jobs() -> list:
    with _STATE_LOCK:
        return list(_load()["jobs"])


def remove_job(job_id: str) -> dict:
    with _STATE_LOCK:
        state = _load()
        before = len(state["jobs"])
        state["jobs"] = [job for job in state["jobs"] if str(job.get("id")) != str(job_id)]
        if len(state["jobs"]) == before:
            return {"ok": False, "error": "job_not_found"}
        _save(state)
        return {"ok": True}


def toggle_job(job_id: str, enabled: bool) -> dict:
    with _STATE_LOCK:
        state = _load()
        for job in state["jobs"]:
            if str(job.get("id")) == str(job_id):
                job["enabled"] = bool(enabled)
                _save(state)
                return {"ok": True, "job_id": str(job_id), "enabled": bool(enabled)}
        return {"ok": False, "error": "job_not_found"}


def cron_status() -> dict:
    try:
        state = _load()
    except ValueError:
        return {
            "ok": False,
            "status": "unavailable",
            "error": "schedule_store_unavailable",
            "running": _running,
            "jobs": 0,
            "enabled_jobs": 0,
            "recent_log": [],
        }
    return {
        "ok": True,
        "status": "healthy",
        "running": _running,
        "jobs": len(state["jobs"]),
        "enabled_jobs": sum(bool(job.get("enabled")) for job in state["jobs"]),
        "recent_log": state.get("log", [])[-10:],
    }


def _should_run(job: dict) -> bool:
    now = time.localtime()
    if now.tm_hour != job.get("hour", -1) or now.tm_min != job.get("minute", 0):
        return False
    if now.tm_wday >= len(_DAY_NAMES) or _DAY_NAMES[now.tm_wday] not in job.get("days", _DAY_NAMES):
        return False
    try:
        last = float(job.get("last_run") or 0)
    except (TypeError, ValueError, OverflowError):
        last = 0
    return time.time() - last >= 55


def _execute_job(job: dict):
    """Run only low-risk scheduled actions; never auto-approve arbitrary proposals."""
    action = job.get("action")
    if action not in SCHEDULED_AUTO_APPROVE_ACTIONS:
        return {"ok": False, "error": "action_not_allowlisted"}
    try:
        from executor.nous_drive import think, approve_proposal, list_proposals

        think(force=True)
        for proposal in list_proposals():
            if proposal.get("action") == action and proposal.get("status") == "pending":
                return approve_proposal(str(proposal["id"]))
        return {"ok": False, "error": "matching_pending_proposal_not_found"}
    except Exception as exc:
        return {"ok": False, "error": f"scheduled_action_failed:{type(exc).__name__}"}


def _scheduler_loop():
    global _running
    while _running:
        try:
            due_jobs = []
            with _STATE_LOCK:
                state = _load()
                changed = False
                for job in state["jobs"]:
                    if job.get("enabled") and _should_run(job):
                        job["last_run"] = time.time()
                        changed = True
                        state.setdefault("log", []).append({
                            "time": time.strftime("%Y-%m-%d %H:%M"),
                            "job": job.get("name", "Unnamed job"),
                            "action": job.get("action", ""),
                        })
                        due_jobs.append(dict(job))
                state["log"] = state.get("log", [])[-200:]
                if changed:
                    _save(state)
            for job in due_jobs:
                threading.Thread(target=_execute_job, args=(job,), daemon=True).start()
        except Exception:
            # Preserve the state file and retry on the next tick; status exposes
            # storage failures rather than silently rebuilding an empty schedule.
            pass
        time.sleep(30)


def start_scheduler():
    global _scheduler_thread, _running
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _running = True
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True, name="nous_cron")
    _scheduler_thread.start()


def stop_scheduler():
    global _running
    _running = False
