def run_plugin(fn):
    try:
        return fn()
    except Exception as e:
        return {"plugin_error": str(e)}
