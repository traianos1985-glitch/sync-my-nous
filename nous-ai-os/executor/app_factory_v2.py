import time

from executor.app_builder import make_web_app, list_apps
from executor.task_queue import add_task
from executor.memory import save


def create_app_from_idea(idea):
    text = str(idea).strip()

    result = make_web_app(text)

    save({
        "event": "app_factory_v2_create",
        "idea": text,
        "result": result,
    })

    return {
        "idea": text,
        "result": result,
        "apps": list_apps(),
        "time": time.time(),
    }


def queue_app_idea(idea, priority=4):
    item = add_task(
        title=f"Φτιάξε εφαρμογή: {idea}",
        kind="app_factory",
        priority=priority,
        payload={"idea": idea}
    )

    return item


def app_factory_status():
    return {
        "apps": list_apps(),
        "time": time.time(),
    }
