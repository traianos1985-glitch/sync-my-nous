import ast
import time
from pathlib import Path

from executor.llm_core import ask
from executor.plugin_builder import create_plugin

BLOCKED = ["os.system", "subprocess.Popen", "rm -rf", "pip install", "eval(", "exec("]


def clean(code):
    return str(code).replace("```python", "").replace("```", "").strip()


def safe_check(code):
    for blocked in BLOCKED:
        if blocked in code:
            return False, f"blocked keyword: {blocked}"
    try:
        ast.parse(code)
        return True, "ok"
    except (SyntaxError, ValueError, TypeError) as exc:
        return False, str(exc)


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


def _validate_source(source, filename="<generated>"):
    try:
        tree = ast.parse(source, filename=filename)
        has_run = any(
            isinstance(node, ast.FunctionDef) and node.name == "run"
            for node in tree.body
        )
        if not has_run:
            return {"success": False, "error": "missing top-level run() function"}
        return {
            "success": True,
            "result": {
                "validation": "static_only",
                "run_function_found": True,
            },
            "execution_skipped": True,
        }
    except (SyntaxError, ValueError, TypeError) as exc:
        return {"success": False, "error": str(exc)}


def test_code(path):
    """Statically validate a generated plugin; never execute generated source."""
    try:
        source = Path(path).read_text(encoding="utf-8")
    except (OSError, ValueError, TypeError) as exc:
        return {"success": False, "error": str(exc)}
    return _validate_source(source, filename=str(path))


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
    code = generate_code(goal)
    ok, msg = safe_check(code)

    if not ok:
        return {"success": False, "stage": "safe_check", "error": msg, "code": code}

    test = _validate_source(code)
    if not test.get("success"):
        fixed = fix_code(goal, code, test.get("error"))
        ok, msg = safe_check(fixed)
        if not ok:
            return {
                "success": False,
                "stage": "fix_safe_check",
                "error": msg,
                "code": fixed,
            }
        code = fixed
        test = _validate_source(code)

    if not test.get("success"):
        return {"success": False, "stage": "final_test", "test": test}

    created = create_plugin(name, code)
    if not created.get("success"):
        return {
            "success": False,
            "stage": "save_plugin",
            "error": created.get("error", "plugin_creation_failed"),
        }

    return {
        "success": True,
        "plugin": created["plugin"],
        "path": created["path"],
        "test": test,
    }
