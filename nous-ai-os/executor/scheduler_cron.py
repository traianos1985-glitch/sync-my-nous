"""Scheduler Cron — αυτόματη εκτέλεση εργασιών NOUS σε προγραμματισμένες ώρες."""
import json, time, threading
from pathlib import Path

SCHEDULE_FILE = Path("data/scheduler_cron.json")
_scheduler_thread: threading.Thread | None = None
_running = False

DEFAULT_JOBS = [
    {"name": "Πρωινή Αναφορά",  "action": "generate_morning_brief",   "hour": 8,  "minute": 0},
    {"name": "Βραδινή Αναφορά", "action": "generate_evening_summary",  "hour": 21, "minute": 0},
    {"name": "Νυχτερινό Backup","action": "create_backup",             "hour": 2,  "minute": 0},
    {"name": "Αυτο-αναστοχασμός","action": "self_reflection",          "hour": 12, "minute": 0},
]


def _load() -> dict:
    if SCHEDULE_FILE.exists():
        try:
            return json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Bootstrap with sensible defaults
    s: dict = {"jobs": [], "log": []}
    for j in DEFAULT_JOBS:
        s["jobs"].append({
            "id":       int(time.time_ns()) + DEFAULT_JOBS.index(j),
            "name":     j["name"],
            "action":   j["action"],
            "hour":     j["hour"],
            "minute":   j["minute"],
            "days":     ["mon","tue","wed","thu","fri","sat","sun"],
            "enabled":  True,
            "created":  time.time(),
            "last_run": None,
        })
    _save(s)
    return s


def _save(s: dict):
    SCHEDULE_FILE.parent.mkdir(exist_ok=True)
    SCHEDULE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def add_job(name: str, action: str, hour: int, minute: int = 0,
            days: list | None = None) -> dict:
    s = _load()
    job = {
        "id":       int(time.time_ns()),
        "name":     name,
        "action":   action,
        "hour":     hour,
        "minute":   minute,
        "days":     days or ["mon","tue","wed","thu","fri","sat","sun"],
        "enabled":  True,
        "created":  time.time(),
        "last_run": None,
    }
    s["jobs"].append(job)
    _save(s)
    return job


def list_jobs() -> list:
    return _load()["jobs"]


def remove_job(job_id: str) -> dict:
    s = _load()
    before = len(s["jobs"])
    s["jobs"] = [j for j in s["jobs"] if str(j["id"]) != str(job_id)]
    _save(s)
    return {"ok": len(s["jobs"]) < before}


def toggle_job(job_id: str, enabled: bool) -> dict:
    s = _load()
    for j in s["jobs"]:
        if str(j["id"]) == str(job_id):
            j["enabled"] = enabled
    _save(s)
    return {"ok": True}


def cron_status() -> dict:
    s = _load()
    return {
        "running":      _running,
        "jobs":         len(s["jobs"]),
        "enabled_jobs": len([j for j in s["jobs"] if j.get("enabled")]),
        "recent_log":   s.get("log", [])[-10:],
    }


def _should_run(job: dict) -> bool:
    now = time.localtime()
    if now.tm_hour   != job.get("hour", -1):  return False
    if now.tm_min    != job.get("minute", 0): return False
    day_names = ["mon","tue","wed","thu","fri","sat","sun"]
    if day_names[now.tm_wday] not in job.get("days", day_names): return False
    last = job.get("last_run") or 0
    if time.time() - last < 55: return False  # debounce
    return True


def _execute_job(job: dict):
    """Εκτελεί μια εργασία — δημιουργεί proposal στο nous_drive και το εγκρίνει."""
    try:
        from executor.nous_drive import think, approve_proposal, list_proposals
        # Force a think cycle then approve the matching action
        think(force=True)
        for p in list_proposals():
            if p.get("action") == job["action"] and p.get("status") == "pending":
                approve_proposal(str(p["id"]))
                break
    except Exception as e:
        pass  # log silently


def _scheduler_loop():
    global _running
    while _running:
        try:
            s = _load()
            changed = False
            for job in s["jobs"]:
                if job.get("enabled") and _should_run(job):
                    job["last_run"] = time.time()
                    changed = True
                    entry = {
                        "time":   time.strftime("%Y-%m-%d %H:%M"),
                        "job":    job["name"],
                        "action": job["action"],
                    }
                    s.setdefault("log", []).append(entry)
                    s["log"] = s["log"][-200:]
                    threading.Thread(target=_execute_job, args=(dict(job),), daemon=True).start()
            if changed:
                _save(s)
        except Exception:
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
