import json
import os
import time

from executor.task_queue import list_queue
from executor.project_progress import project_summary
from executor.autonomy_service import status as service_status
from executor.scheduler_agent import list_schedules
from executor.battery_guard import battery_guard

FILE = "data/runtime_metrics.json"


def collect_metrics():
    queue = list_queue()
    projects = project_summary()
    service = service_status()
    schedules = list_schedules()
    battery = battery_guard()

    metrics = {
        "time": time.time(),
        "battery": battery,
        "service": service,
        "queue": {
            "total": len(queue),
            "pending": len([x for x in queue if x.get("status") == "pending"]),
            "running": len([x for x in queue if x.get("status") == "running"]),
            "done": len([x for x in queue if x.get("status") == "done"]),
            "failed": len([x for x in queue if x.get("status") == "failed"]),
        },
        "projects": projects,
        "schedules": {
            "total": len(schedules),
            "scheduled": len([x for x in schedules if x.get("status") == "scheduled"]),
        },
    }

    os.makedirs("data", exist_ok=True)
    json.dump(metrics, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return metrics
