import time
from executor.memory import save

RUNNING = False
LAST_RUN = None
LAST_RESULT = None


def start():
    global RUNNING
    RUNNING = True

    save({
        "event": "autonomy_started",
        "time": time.time()
    })

    return "AUTONOMY_STARTED"


def stop():
    global RUNNING
    RUNNING = False

    save({
        "event": "autonomy_stopped",
        "time": time.time()
    })

    return "AUTONOMY_STOPPED"


def status():
    return {
        "running": RUNNING,
        "last_run": LAST_RUN,
        "has_last_result": LAST_RESULT is not None,
    }


def mark_run(result):
    global LAST_RUN, LAST_RESULT
    LAST_RUN = time.time()
    LAST_RESULT = result

    save({
        "event": "autonomy_loop_run",
        "time": LAST_RUN,
        "result_keys": list(result.keys()) if isinstance(result, dict) else []
    })

    return result
