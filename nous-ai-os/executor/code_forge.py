import os, ast, time, subprocess
from executor.llm_core import ask

WORKDIR = "forge"
os.makedirs(WORKDIR, exist_ok=True)

BLOCKED = ["os.system", "subprocess.Popen", "rm -rf", "pip install", "eval(", "exec("]

def clean(code):
    return str(code).replace("```python", "").replace("```", "").strip()

def safe_check(code):
    for b in BLOCKED:
        if b in code:
            return False, f"blocked keyword: {b}"
    try:
        ast.parse(code)
        return True, "ok"
    except Exception as e:
        return False, str(e)

def generate_code(goal):
    prompt = f"""
Write only valid Python code.
No markdown.
No explanation.

Goal:
{goal}

Rules:
- safe code only
- no os.system
- no pip install
- no eval
- no exec
- include a run() function
- run() must return a dict
"""
    res = ask(prompt)
    return clean(res.get("response", str(res)) if isinstance(res, dict) else str(res))

def test_code(path):
    try:
        subprocess.check_output(["python", "-m", "py_compile", path], stderr=subprocess.STDOUT, text=True, timeout=10)
        code = open(path, "r", encoding="utf-8").read()
        ns = {}
        exec(code, ns)
        if "run" not in ns:
            return {"success": False, "error": "missing run()"}
        out = ns["run"]()
        return {"success": True, "result": out}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fix_code(goal, code, error):
    prompt = f"""
Fix this Python code.
Return only valid Python code.
No markdown.
Must include run() returning dict.

Goal:
{goal}

Error:
{error}

Code:
{code}
"""
    res = ask(prompt)
    return clean(res.get("response", str(res)) if isinstance(res, dict) else str(res))

def forge_plugin(goal):
    name = "forge_plugin_" + str(int(time.time()))
    path = f"{WORKDIR}/{name}.py"

    code = generate_code(goal)
    ok, msg = safe_check(code)

    if not ok:
        return {"success": False, "stage": "safe_check", "error": msg, "code": code}

    open(path, "w", encoding="utf-8").write(code)
    test = test_code(path)

    if not test.get("success"):
        fixed = fix_code(goal, code, test.get("error"))
        ok, msg = safe_check(fixed)

        if not ok:
            return {"success": False, "stage": "fix_safe_check", "error": msg, "code": fixed}

        open(path, "w", encoding="utf-8").write(fixed)
        test = test_code(path)

    if not test.get("success"):
        return {"success": False, "stage": "final_test", "test": test, "path": path}

    final = f"executor/plugins/{name}.py"
    os.makedirs("executor/plugins", exist_ok=True)
    open(final, "w", encoding="utf-8").write(open(path, "r", encoding="utf-8").read())

    return {"success": True, "plugin": name, "path": final, "test": test}
