from executor.self_heal import auto_heal

def safe_execute(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        auto_heal(e)
        return {
            "status": "recovered",
            "error": str(e)
        }
