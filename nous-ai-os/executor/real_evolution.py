import os
import time
import ast
import traceback

from executor.local_llm import ask_llm
from executor.plugin_loader import load_plugins


PLUGIN_DIR = "plugins"


class RealEvolutionEngine:

    def __init__(self):

        self.history = []

    def clean_code(self, code):

        code = str(code)

        code = code.replace("```python", "")
        code = code.replace("```", "")

        return code.strip()

    def validate_python(self, code):

        try:

            ast.parse(code)

            return True, None

        except Exception as e:

            return False, str(e)

    def validate_plugin(self, code):

        if "def run" not in code:

            return False, "missing run()"

        return True, None

    def generate_plugin_code(self, goal):

        prompt = f"""
Create SAFE Python plugin.

GOAL:
{goal}

STRICT RULES:
- valid python only
- MUST contain run()
- no markdown
- no explanations
- no imports except safe stdlib
- return dict
"""

        result = ask_llm(prompt)

        return self.clean_code(result)

    def save_plugin(self, name, code):

        path = os.path.join(
            PLUGIN_DIR,
            f"{name}.py"
        )

        with open(path, "w") as f:

            f.write(code)

        return path

    def evolve(self, goal):

        timestamp = int(time.time())

        plugin_name = f"evolved_{timestamp}"

        code = self.generate_plugin_code(goal)

        valid_py, py_error = self.validate_python(code)

        if not valid_py:

            return {

                "status": "python_validation_failed",

                "error": py_error,

                "code": code
            }

        valid_plugin, plugin_error = self.validate_plugin(code)

        if not valid_plugin:

            return {

                "status": "plugin_validation_failed",

                "error": plugin_error,

                "code": code
            }

        path = self.save_plugin(
            plugin_name,
            code
        )

        load_plugins()

        result = {

            "status": "plugin_created",

            "plugin": plugin_name,

            "path": path
        }

        self.history.append(result)

        return result
