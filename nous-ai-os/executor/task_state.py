import time

from executor.json_state_store import edit_list, read_list, write_list

FILE = "data/tasks.json"


def _load():
    return read_list(FILE)


def _save(tasks):
    return write_list(FILE, tasks)


def add_task(text):
    with edit_list(FILE) as tasks:
        task_id = time.time_ns()
        used = {str(item.get("id")) for item in tasks}
        while str(task_id) in used:
            task_id += 1
        item = {"id": task_id, "task": text, "status": "open"}
        tasks.append(item)
    return item


def list_tasks():
    return _load()


def close_task(task_id):
    with edit_list(FILE) as tasks:
        for task in tasks:
            if str(task.get("id")) == str(task_id):
                task["status"] = "closed"
    return _load()
