import os
import time
import traceback

from executor.local_llm import ask_llm
from executor.secure_patch import secure_patch


class SelfHealV2:

    def __init__(self):

        self.last_error = None

    def analyze_system(self):

        # simple health check: router exists & imports OK

        checks = []

        try:

            import executor.router

            checks.append(("router_import", True))

        except Exception as e:

            checks.append(("router_import", False))
            self.last_error = traceback.format_exc()

        return checks

    def diagnose(self, error):

        prompt = f"""
You are a system debugger.

Find root cause and fix.

ERROR:
{error}

Return:
1. cause
2. fix
3. safe patch (if needed)
"""

        return ask_llm(prompt)

    def attempt_heal(self):

        status = self.analyze_system()

        failed = [c for c in status if not c[1]]

        if not failed:

            return {
                "status": "healthy",
                "message": "no issues detected"
            }

        error = self.last_error or "unknown error"

        diagnosis = self.diagnose(error)

        return {
            "status": "unhealthy",
            "diagnosis": diagnosis
        }

    def heal_file(self, file_path, fixed_code, auto_apply=False):

        if not auto_apply:

            return {
                "status": "fix_proposed",
                "file": file_path,
                "patch": fixed_code
            }

        try:

            result = secure_patch(file_path, fixed_code)

            return {
                "status": "patched" if result else "failed",
                "file": file_path
            }

        except Exception as e:

            return {
                "status": "patch_error",
                "error": str(e)
            }
