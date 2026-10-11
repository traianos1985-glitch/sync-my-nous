import ast
import re
from pathlib import Path

PLUGIN_DIR = "executor/plugins"
_PLUGIN_NAME = re.compile(r"[A-Za-z0-9_-]{1,80}\\Z")


def clean_code(code):
    return str(code).replace("```python", "").replace("```", "").strip()


def validate(code):
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, TypeError) as exc:
        return False, str(exc)
    if not any(
        isinstance(node, ast.FunctionDef) and node.name == "run"
        for node in tree.body
    ):
        return False, "missing top-level run() function"
    if "pip" in code or "os.system" in code or "subprocess" in code:
        return False, "blocked unsafe keyword"
    return True, "ok"


def create_plugin(name, code):
    code = clean_code(code)
    ok, msg = validate(code)
    if not ok:
        return {"success": False, "error": msg, "code": code}
    if not isinstance(name, str) or not _PLUGIN_NAME.fullmatch(name):
        return {"success": False, "error": "invalid_plugin_name"}

    root = Path(PLUGIN_DIR).resolve()
    try:
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{name}.py"
        if path.parent != root:
            return {"success": False, "error": "invalid_plugin_path"}
        # Exclusive creation refuses existing files and symlinks (O_EXCL),
        # avoiding accidental overwrite through a symlink or name collision.
        with path.open("x", encoding="utf-8") as stream:
            stream.write(code)
    except FileExistsError:
        return {"success": False, "error": "plugin_already_exists"}
    except OSError as exc:
        return {"success": False, "error": str(exc)}

    return {"success": True, "plugin": name, "path": str(path)}
