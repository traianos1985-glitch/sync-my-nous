import json, os, time

FILE="data/tasks.json"

def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE,"r",encoding="utf-8"))
    except:
        return []

def _save(tasks):
    os.makedirs("data",exist_ok=True)
    json.dump(tasks,open(FILE,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

def add_task(text):
    tasks=_load()
    item={"id":int(time.time()),"task":text,"status":"open"}
    tasks.append(item)
    _save(tasks)
    return item

def list_tasks():
    return _load()

def close_task(task_id):
    tasks=_load()
    for t in tasks:
        if str(t.get("id"))==str(task_id):
            t["status"]="closed"
    _save(tasks)
    return tasks
