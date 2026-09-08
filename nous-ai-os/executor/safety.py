def safe_run(fn, fallback=None):
    try:
        return fn()
    except Exception as e:
        return {
            "error": str(e),
            "fallback": fallback
        }
