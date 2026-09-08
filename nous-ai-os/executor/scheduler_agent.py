import json
import os
import time
import re
from datetime import datetime, timedelta

FILE = "data/scheduled_tasks.json"


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(tasks):
    os.makedirs("data", exist_ok=True)
    json.dump(tasks, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _today_at(hour, minute):
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)
    return target.timestamp()


def _next_daily_run(hour, minute):
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
    return target.timestamp()


def parse_schedule(text):
    raw = str(text).strip()
    lower = raw.lower()

    time_match = re.search(r"(\d{1,2}):(\d{2})", lower)
    hour = None
    minute = None

    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))

    every_minutes = re.search(r"κάθε\s+(\d+)\s+λεπ", lower) or re.search(r"every\s+(\d+)\s+min", lower)
    if every_minutes:
        interval = int(every_minutes.group(1))
        task = re.sub(r"κάθε\s+\d+\s+λεπ\w*", "", raw, flags=re.I).strip()
        task = re.sub(r"every\s+\d+\s+min\w*", "", task, flags=re.I).strip()
        return {
            "task": task or raw,
            "schedule_type": "interval",
            "hour": None,
            "minute": None,
            "interval_seconds": interval * 60,
            "next_run": time.time() + interval * 60,
        }

    if "κάθε ώρα" in lower or "every hour" in lower or "hourly" in lower:
        task = raw
        task = re.sub(r"κάθε ώρα", "", task, flags=re.I).strip()
        task = re.sub(r"every hour|hourly", "", task, flags=re.I).strip()
        return {
            "task": task or raw,
            "schedule_type": "interval",
            "hour": None,
            "minute": None,
            "interval_seconds": 3600,
            "next_run": time.time() + 3600,
        }

    if "κάθε μέρα" in lower or "daily" in lower or "every day" in lower:
        if hour is None:
            hour = 9
            minute = 0

        task = raw
        task = re.sub(r"κάθε μέρα", "", task, flags=re.I).strip()
        task = re.sub(r"^\s*(daily|every day)\s+", "", task, flags=re.I).strip()
        task = re.sub(r"στις\s+\d{1,2}:\d{2}", "", task, flags=re.I).strip()
        task = re.sub(r"at\s+\d{1,2}:\d{2}", "", task, flags=re.I).strip()

        return {
            "task": task or raw,
            "schedule_type": "daily",
            "hour": hour,
            "minute": minute,
            "interval_seconds": None,
            "next_run": _today_at(hour, minute),
        }

    return {
        "task": raw,
        "schedule_type": "manual",
        "hour": None,
        "minute": None,
        "interval_seconds": None,
        "next_run": None,
    }


def add_schedule(text):
    tasks = _load()
    parsed = parse_schedule(text)

    item = {
        "id": time.time_ns(),
        "task": parsed["task"],
        "raw": str(text).strip(),
        "status": "scheduled",
        "schedule_type": parsed["schedule_type"],
        "hour": parsed["hour"],
        "minute": parsed["minute"],
        "interval_seconds": parsed.get("interval_seconds"),
        "next_run": parsed["next_run"],
        "created": time.time(),
        "last_run": None,
    }

    tasks.append(item)
    _save(tasks)
    return item


def list_schedules():
    return _load()


def clear_schedules():
    _save([])
    return {"cleared": True}


def execute_scheduled_task(task_text):
    text = str(task_text).strip().lower()

    if text == "daily brief" or text == "ημερήσια εικόνα":
        from executor.daily_brief import daily_brief
        return daily_brief()

    if text == "repair system" or text == "επισκευή συστήματος":
        from executor.repair_agent import repair_check
        return repair_check()

    if text == "battery guard" or text == "έλεγχος μπαταρίας":
        from executor.battery_guard import battery_guard
        return battery_guard()

    return {
        "status": "skipped",
        "reason": "unknown scheduled task",
        "task": task_text,
    }


def run_due_schedules(now=None):
    if now is None:
        now = time.time()

    tasks = _load()
    executed = []

    for item in tasks:
        if item.get("status") != "scheduled":
            continue

        next_run = item.get("next_run")
        if not next_run:
            continue

        if float(next_run) <= float(now):
            result = execute_scheduled_task(item.get("task", ""))

            item["last_run"] = now
            item["last_result"] = result

            if item.get("schedule_type") == "daily":
                item["next_run"] = _next_daily_run(
                    int(item.get("hour", 9)),
                    int(item.get("minute", 0)),
                )
            elif item.get("schedule_type") == "interval":
                item["next_run"] = float(now) + int(item.get("interval_seconds", 3600))
            else:
                item["status"] = "done"

            executed.append({
                "id": item.get("id"),
                "task": item.get("task"),
                "result": result,
            })

    _save(tasks)

    return {
        "checked": len(tasks),
        "executed": executed,
    }
