import json
import os

MEMORY_FILE = "data/memory.json"

def load():
    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save(entry):

    mem = load()
    mem.append(entry)

    mem = mem[-200:]

    with open(MEMORY_FILE,"w",encoding="utf-8") as f:
        json.dump(mem,f,ensure_ascii=False,indent=2)
