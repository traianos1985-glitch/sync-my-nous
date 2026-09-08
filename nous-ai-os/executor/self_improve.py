from executor.plugin_creator import create_plugin
from executor.codegen import generate_plugin

def improve(goal):

    if "plugin" in goal:
        code = generate_plugin("auto_plugin", "pass")
        return create_plugin("auto_plugin", code)

    return {"status": "no_improvement"}
