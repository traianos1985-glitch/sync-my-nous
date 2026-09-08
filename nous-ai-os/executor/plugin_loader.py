import os
import importlib.util

PLUGIN_DIR = "executor/plugins"

def load_plugins():
    plugins = {}

    for file in os.listdir(PLUGIN_DIR):
        if file.endswith(".py"):
            path = os.path.join(PLUGIN_DIR, file)
            name = file[:-3]

            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            if hasattr(mod, "run"):
                plugins[name] = mod.run

    return plugins
