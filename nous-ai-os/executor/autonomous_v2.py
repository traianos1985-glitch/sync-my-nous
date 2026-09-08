from executor.plugin_creator import create_plugin
from executor.codegen import generate_plugin
from executor.plugin_loader import load_plugins

def execute_task(task: str):

    task = str(task).lower()

    # 1. create plugin
    if "plugin" in task and "create" in task:
        code = generate_plugin("auto_plugin", "pass")
        return create_plugin("auto_plugin", code)

    # 2. load plugins
    if "load" in task:
        return {"plugins": list(load_plugins().keys())}

    # 3. evolve behavior (safe stub)
    if "evolve" in task:
        return {
            "status": "evolving",
            "mode": "controlled"
        }

    return {
        "status": "idle",
        "task": task
    }
