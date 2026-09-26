import json
import os
from executor.sqlite_store import save_memory, load_memories

MEMORY_FILE = "data/memory.json"

def load():
    try:
        mem = load_memories()
        if mem:
            return mem
    except Exception:
        pass

    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save(entry):
    try:
        save_memory(entry)
    except Exception:
        pass

    mem = load()
    mem.append(entry)
    mem = mem[-200:]
    try:
        os.makedirs("data", exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
