import importlib.util
import re
from pathlib import Path

PLUGIN_DIR = "executor/plugins"
_PLUGIN_NAME = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")


def _plugin_path(name):
    if not isinstance(name, str) or not _PLUGIN_NAME.fullmatch(name):
        return None

    root = Path(PLUGIN_DIR).resolve()
    candidate = root / f"{name}.py"
    # Refuse symlinks even when they point to another file inside this directory.
    if candidate.is_symlink() or not candidate.is_file():
        return None
    path = candidate.resolve()
    if path.parent != root:
        return None
    return path


def list_plugins():
    root = Path(PLUGIN_DIR).resolve()
    if not root.is_dir():
        return []
    return sorted(
        path.stem
        for path in root.iterdir()
        if path.is_file()
        and not path.is_symlink()
        and path.resolve().parent == root
        and path.suffix == ".py"
        and _PLUGIN_NAME.fullmatch(path.stem)
    )


def load_plugin(name):
    path = _plugin_path(name)
    if path is None:
        return None
    module_name = f"nous_plugin_{name}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_plugin(name, *args, **kwargs):
    module = load_plugin(name)
    if module is None:
        return {"success": False, "error": "plugin_not_found"}
    if not hasattr(module, "run"):
        return {"success": False, "error": "plugin_has_no_run"}
    try:
        return module.run(*args, **kwargs)
    except Exception as exc:
        return {"success": False, "error": str(exc)}
