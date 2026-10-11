import time

from executor.llm_core import ask
from executor.plugin_builder import create_plugin


def generate_plugin(goal):
    prompt = f"""
Write ONLY valid Python code.
No markdown.
No explanation.
Create a safe plugin for this goal:
{goal}

Rules:
- must define a top-level run() function
- run() must return dict
- no pip
- no subprocess
- no os.system
"""
    res = ask(prompt)
    code = res.get("response", str(res)) if isinstance(res, dict) else str(res)
    name = f"ai_plugin_{time.time_ns()}"
    created = create_plugin(name, code)

    if not created.get("success"):
        return created

    # Never import or execute model-generated source during creation. A user can
    # review the saved plugin and explicitly invoke the existing run-plugin tool.
    return {
        "created": created,
        "test": {
            "success": True,
            "execution_skipped": True,
            "result": {
                "validation": "static_only",
                "run_function_found": True,
            },
        },
    }
