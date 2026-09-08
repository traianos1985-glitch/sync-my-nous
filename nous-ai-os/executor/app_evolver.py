import time

from executor.app_builder import list_apps
from executor.task_queue import add_task
from executor.memory import save


def app_evolution_status():
    return {
        "apps": list_apps(),
        "time": time.time(),
        "mode": "planning_only",
    }


def queue_app_improvement(app_name, request="βελτίωσε την εφαρμογή", priority=4):
    item = add_task(
        title=f"Βελτίωσε app: {app_name}",
        kind="app_improvement",
        priority=priority,
        payload={
            "app": app_name,
            "request": request,
        },
    )

    save({
        "event": "app_improvement_queued",
        "app": app_name,
        "request": request,
    })

    return item
