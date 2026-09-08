import time
from executor.llm_core import ask
from executor.plugin_builder import create_plugin
from executor.plugin_tester import test_plugin

def generate_plugin(goal):
    prompt = f"""
Write ONLY valid Python code.
No markdown.
No explanation.
Create a safe plugin for this goal:
{goal}

Rules:
- must define run()
- run() must return dict
- no pip
- no subprocess
- no os.system
"""
    res = ask(prompt)
    code = res.get("response", str(res)) if isinstance(res, dict) else str(res)
    name = f"ai_plugin_{int(time.time())}"
    created = create_plugin(name, code)

    if not created.get("success"):
        return created

    tested = test_plugin(created["plugin"])
    return {"created": created, "test": tested}
