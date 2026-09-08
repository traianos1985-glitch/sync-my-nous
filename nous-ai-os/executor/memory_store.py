import json
import os

MEM_FILE = "executor/memory.json"

def load():
    if not os.path.exists(MEM_FILE):
        return {}
    return json.load(open(MEM_FILE))

def save(data):
    with open(MEM_FILE, "w") as f:
        json.dump(data, f, indent=2)

def set_mem(key, value):
    data = load()
    data[key] = value
    save(data)
    return data

def get_mem(key, default=None):
    return load().get(key, default)
