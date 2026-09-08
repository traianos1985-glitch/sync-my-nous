import os
import importlib.util

PLUGIN_DIR = "executor/plugins"

def list_plugins():
    if not os.path.exists(PLUGIN_DIR):
        return []
    return [f[:-3] for f in os.listdir(PLUGIN_DIR) if f.endswith(".py")]

def load_plugin(name):
    path = os.path.join(PLUGIN_DIR, name + ".py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def run_plugin(name, *args, **kwargs):
    mod = load_plugin(name)
    if mod is None:
        return {"success": False, "error": "plugin_not_found"}
    if not hasattr(mod, "run"):
        return {"success": False, "error": "plugin_has_no_run"}
    try:
        return mod.run(*args, **kwargs)
    except Exception as e:
        return {"success": False, "error": str(e)}
