def run_code(code):
    try:
        local = {}
        exec(code, {}, local)
        return {"output": local}
    except Exception as e:
        return {"error": str(e)}
