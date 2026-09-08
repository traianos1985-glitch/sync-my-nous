import os
import time
import traceback

from executor.memory import add_event
from executor.secure_patch import secure_patch


class AutonomousEngine:

    def __init__(self):

        self.running = False

    def system_analysis(self):

        missing = []

        targets = [
            ("executor/plugin_loader.py", "plugin system"),
            ("executor/self_healing.py", "self healing"),
            ("executor/local_llm.py", "local llm bridge"),
            ("executor/command_parser.py", "advanced parser")
        ]

        for file, desc in targets:

            if not os.path.exists(file):

                missing.append({
                    "file": file,
                    "description": desc
                })

        return missing

    def generate_code(self, target):

        file = target["file"]

        if "plugin_loader" in file:

            return '''
import os
import importlib

PLUGIN_DIR = "plugins"

def load_plugins():

    loaded = []

    if not os.path.exists(PLUGIN_DIR):
        os.makedirs(PLUGIN_DIR)

    for file in os.listdir(PLUGIN_DIR):

        if file.endswith(".py"):

            name = file[:-3]

            module = importlib.import_module(
                f"plugins.{name}"
            )

            loaded.append(name)

    return loaded
'''

        if "self_healing" in file:

            return '''
import subprocess
import time

def restart_server():

    subprocess.Popen(
        ["python", "executor/router.py"]
    )

    return True
'''

        if "local_llm" in file:

            return '''
def ask_llm(prompt):

    return {
        "mock_response": prompt
    }
'''

        if "command_parser" in file:

            return '''
def parse_command(text):

    parts = text.split()

    return {
        "command": parts[0],
        "args": parts[1:]
    }
'''

        return "# empty"

    def evolve_once(self):

        upgrades = []

        missing = self.system_analysis()

        for target in missing:

            try:

                code = self.generate_code(target)

                result = secure_patch(
                    target["file"],
                    code
                )

                upgrades.append({
                    "target": target["description"],
                    "file": target["file"],
                    "success": bool(result)
                })

                add_event(
                    f"Autonomous upgrade: {target['file']}"
                )

            except Exception as e:

                upgrades.append({
                    "target": target["description"],
                    "success": False,
                    "error": str(e)
                })

                traceback.print_exc()

        return {
            "status": "completed",
            "upgrades": upgrades
        }

    def start_loop(self):

        self.running = True

        while self.running:

            self.evolve_once()

            time.sleep(30)

    def stop_loop(self):

        self.running = False

        return {
            "stopped": True
        }
