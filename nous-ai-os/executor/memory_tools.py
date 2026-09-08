from executor.memory import load

def recent(limit=10):
    return load()[-limit:]

def summary():
    mem = load()
    return {
        "total_items": len(mem),
        "recent": mem[-5:]
    }
