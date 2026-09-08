import json, os, time

DB="logs/versions.json"

def _load():
    if not os.path.exists(DB):
        return {"v":[]}
    return json.load(open(DB))

def _save(d):
    os.makedirs("logs", exist_ok=True)
    json.dump(d, open(DB,"w"), indent=2)

def checkpoint(file, content):
    d=_load()
    d["v"].append({"f":file,"c":content,"t":time.time()})
    _save(d)

def last_version(file):
    d=_load()
    for v in reversed(d["v"]):
        if v["f"]==file:
            return v
    return None
