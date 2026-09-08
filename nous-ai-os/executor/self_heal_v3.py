import time
import threading
import traceback
import os
import copy

from executor.local_llm import ask_llm
from executor.secure_patch import secure_patch


class SelfHealV3:

    def __init__(self):

        self.running = False
        self.error_queue = []
        self.snapshots = {}

    # ----------------------------
    # SYSTEM SNAPSHOT
    # ----------------------------

    def snapshot_file(self, path):

        if not os.path.exists(path):

            return None

        with open(path, "r") as f:

            return f.read()

    def save_snapshot(self, path):

        self.snapshots[path] = self.snapshot_file(path)

    def rollback(self, path):

        if path not in self.snapshots:

            return {
                "status": "no_snapshot"
            }

        with open(path, "w") as f:

            f.write(self.snapshots[path])

        return {
            "status": "rolled_back",
            "file": path
        }

    # ----------------------------
    # ERROR HANDLING
    # ----------------------------

    def add_error(self, error, context="unknown"):

        self.error_queue.append({
            "error": error,
            "context": context,
            "time": time.time()
        })

    # ----------------------------
    # AI DIAGNOSIS
    # ----------------------------

    def diagnose(self, error):

        return ask_llm(
            f"""
You are a system auto-repair AI.

Analyze error and propose fix.

ERROR:
{error}

Return:
- root cause
- fix strategy
- safe patch code (ONLY if safe)
"""
        )

    # ----------------------------
    # APPLY PATCH SAFE
    # ----------------------------

    def apply_patch(self, file_path, new_code):

        self.save_snapshot(file_path)

        result = secure_patch(file_path, new_code)

        return result

    # ----------------------------
    # LOOP
    # ----------------------------

    def loop(self):

        self.running = True

        while self.running:

            try:

                if not self.error_queue:

                    time.sleep(3)
                    continue

                item = self.error_queue.pop(0)

                error = item["error"]
                context = item["context"]

                diagnosis = self.diagnose(error)

                # store analysis event
                print("[SELF-HEAL] diagnosing:", context)

                print(diagnosis)

                # NOTE: no auto patching yet (safe mode)
                # could be enabled later

            except Exception as e:

                print("[SELF-HEAL ERROR]", str(e))

                time.sleep(2)

    # ----------------------------
    # CONTROL
    # ----------------------------

    def start(self):

        t = threading.Thread(target=self.loop, daemon=True)
        t.start()

        return {"status": "self_heal_v3_started"}

    def stop(self):

        self.running = False

        return {"status": "stopped"}
