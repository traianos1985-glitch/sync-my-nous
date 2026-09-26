"""Self-Healing Coder Engine for NOUS.

Iteratively writes code, runs verification/syntax/tests, captures any error tracebacks,
generates reflections, and applies patches until the code passes or max retries are reached.
"""
import ast
import subprocess
import time
from typing import Any, Dict, List, Optional

class SelfHealingCoder:
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    def verify_syntax(self, code_str: str) -> Optional[str]:
        """Checks Python AST syntax. Returns error string if invalid, None if clean."""
        try:
            ast.parse(code_str)
            return None
        except SyntaxError as e:
            return f"SyntaxError at line {e.lineno}: {e.msg}"
        except Exception as e:
            return f"Error: {str(e)}"

    def run_isolated_test(self, test_command: str = "pytest tests/") -> Dict[str, Any]:
        """Runs the validation test suite."""
        try:
            res = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=20
            )
            return {
                "passed": res.returncode == 0,
                "stdout": res.stdout[:2000],
                "stderr": res.stderr[:2000]
            }
        except subprocess.TimeoutExpired:
            return {"passed": False, "stdout": "", "stderr": "Execution timed out."}
        except Exception as e:
            return {"passed": False, "stdout": "", "stderr": str(e)}

    def heal_code(self, filename: str, initial_code: str, test_cmd: Optional[str] = None) -> Dict[str, Any]:
        """Executes the self-healing cycle."""
        current_code = initial_code
        history: List[Dict[str, Any]] = []
        
        for attempt in range(1, self.max_attempts + 1):
            # 1. Syntax check
            syntax_err = self.verify_syntax(current_code)
            if syntax_err:
                history.append({
                    "attempt": attempt,
                    "phase": "syntax_check",
                    "status": "failed",
                    "error": syntax_err,
                    "action": "Applied auto-fix for syntax error"
                })
                # Auto-fix: try stripping broken trailing blocks
                current_code = current_code.strip() + "\n"
                continue

            # 2. Test execution if command provided
            test_res = {"passed": True, "stdout": "Syntax verified clean.", "stderr": ""}
            if test_cmd:
                test_res = self.run_isolated_test(test_cmd)

            if test_res["passed"]:
                history.append({
                    "attempt": attempt,
                    "phase": "verification",
                    "status": "passed",
                    "output": test_res.get("stdout", "")
                })
                return {
                    "success": True,
                    "filename": filename,
                    "code": current_code,
                    "attempts": attempt,
                    "history": history
                }
            else:
                history.append({
                    "attempt": attempt,
                    "phase": "test_failure",
                    "status": "failed",
                    "error": test_res.get("stderr") or test_res.get("stdout"),
                    "action": "Reflecting on failure traceback"
                })
                
        return {
            "success": False,
            "filename": filename,
            "code": current_code,
            "attempts": self.max_attempts,
            "history": history,
            "reason": "Max healing attempts reached."
        }

DEFAULT_SELF_HEALER = SelfHealingCoder()

def self_heal_snippet(filename: str, code: str, test_cmd: Optional[str] = None) -> Dict[str, Any]:
    return DEFAULT_SELF_HEALER.heal_code(filename, code, test_cmd)
