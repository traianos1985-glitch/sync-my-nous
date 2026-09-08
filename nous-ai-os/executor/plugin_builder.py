import os, time, ast

PLUGIN_DIR = "executor/plugins"
os.makedirs(PLUGIN_DIR, exist_ok=True)

def clean_code(code):
    return str(code).replace("```python","").replace("```","").strip()

def validate(code):
    try:
        ast.parse(code)
    except Exception as e:
        return False, str(e)
    if "def run" not in code:
        return False, "missing run()"
    if "pip" in code or "os.system" in code or "subprocess" in code:
        return False, "blocked unsafe keyword"
    return True, "ok"

def create_plugin(name, code):
    code = clean_code(code)
    ok, msg = validate(code)
    if not ok:
        return {"success": False, "error": msg, "code": code}

    safe = "".join(c for c in name if c.isalnum() or c == "_") or f"plugin_{int(time.time())}"
    path = f"{PLUGIN_DIR}/{safe}.py"

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

    return {"success": True, "plugin": safe, "path": path}
