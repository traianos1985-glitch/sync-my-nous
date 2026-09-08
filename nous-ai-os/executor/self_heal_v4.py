import os
import time
import traceback

from executor.local_llm import ask_llm
from executor.secure_patch import secure_patch


class SelfHealV4:

    def __init__(self):

        self.snapshots = {}

    # ----------------------------
    # SNAPSHOT SYSTEM
    # ----------------------------

    def snapshot(self, file_path):

        if not os.path.exists(file_path):
            return None

        with open(file_path, "r") as f:
            content = f.read()

        self.snapshots[file_path] = content

    def rollback(self, file_path):

        if file_path not in self.snapshots:
            return {"status": "no_snapshot"}

        with open(file_path, "w") as f:
            f.write(self.snapshots[file_path])

        return {"status": "rolled_back", "file": file_path}

    # ----------------------------
    # AI FIX GENERATION
    # ----------------------------

    def generate_fix(self, error, code):

        return ask_llm(f"""
You are an expert Python engineer.

Fix the following code.

ERROR:
{error}

CODE:
{code}

Return ONLY corrected full code.
""")

    # ----------------------------
    # APPLY + VALIDATE
    # ----------------------------

    def apply_and_test(self, file_path, new_code):

        try:

            self.snapshot(file_path)

            result = secure_patch(file_path, new_code)

            if not result:

                return {"status": "patch_failed"}

            # validation step: syntax check only
            with open(file_path, "r") as f:

                compiled = compile(f.read(), file_path, "exec")

            return {"status": "success"}

        except Exception as e:

            self.rollback(file_path)

            return {
                "status": "failed_rollback",
                "error": str(e)
            }

    # ----------------------------
    # FULL AUTONOMOUS REPAIR
    # ----------------------------

    def repair_file(self, file_path, error_log):

        if not os.path.exists(file_path):

            return {"error": "file not found"}

        with open(file_path, "r") as f:

            code = f.read()

        ai_fix = self.generate_fix(error_log, code)

        return self.apply_and_test(file_path, ai_fix)

    # ----------------------------
    # SYSTEM MODE (manual trigger)
    # ----------------------------

    def run(self, file_path, error_log):

        return self.repair_file(file_path, error_log)
