from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from executor.error_learning_engine import remember_error, remember_solution

REPORTS = Path("data/reports")

DEFAULT_PY_FILES = [
    "executor/router.py",
    "executor/chat_brain_v3.py",
    "executor/knowledge_memory_engine.py",
    "executor/error_learning_engine.py",
    "executor/patch_quality_gate.py",
]

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def run_cmd(cmd: list[str], timeout: int = 60) -> dict:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"ok": p.returncode == 0, "code": p.returncode, "cmd": cmd, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as e:
        return {"ok": False, "code": -1, "cmd": cmd, "stdout": "", "stderr": repr(e)}

def quality_gate(files=None, label="manual") -> dict:
    files = files or DEFAULT_PY_FILES
    files = [f for f in files if Path(f).exists()]

    checks = {
        "py_compile": run_cmd(["python", "-m", "py_compile", *files]) if files else {"ok": True, "skipped": True},
        "imports": run_cmd(["python", "-c", "import executor.router, executor.chat_brain_v3, executor.knowledge_memory_engine, executor.error_learning_engine, executor.patch_quality_gate; print('IMPORTS_OK')"]),
        "routes": run_cmd(["python", "-c", "from executor.router import app; c=app.test_client(); assert c.get('/remote/knowledge/status').status_code < 500; print('ROUTES_OK')"]),
        "chat": run_cmd(["python", "-c", "from executor.chat_brain_v3 import answer_chat; r=answer_chat('Τι κάνεις;'); assert r and r.get('ok'); assert answer_chat('/plan test') is None; print('CHAT_OK')"]),
        "git_diff": run_cmd(["git", "diff", "--stat"]),
    }

    ok = all(v.get("ok") for k, v in checks.items() if k != "git_diff")

    result = {
        "ok": ok,
        "tool": "Patch Quality Gate",
        "label": label,
        "timestamp": now_iso(),
        "files": files,
        "checks": checks,
    }

    report = REPORTS / f"patch_quality_gate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report, result)
    result["report_path"] = str(report)

    if ok:
        remember_solution(
            problem=f"quality gate passed: {label}",
            solution="py_compile/imports/routes/chat smoke passed",
            files=files,
            status="successful",
            tags=["quality_gate", "validation"],
        )
    else:
        for name, check in checks.items():
            if name != "git_diff" and not check.get("ok"):
                remember_error(
                    error_type=f"quality_gate_{name}",
                    message=check.get("stderr") or check.get("stdout") or "unknown failure",
                    file=", ".join(files),
                    command=" ".join(check.get("cmd", [])),
                    fix="Fix failing module and rerun quality gate.",
                    status="open",
                    tags=["quality_gate", name],
                )

    return result

if __name__ == "__main__":
    import sys
    print(json.dumps(quality_gate(sys.argv[1:] or None, label="cli"), indent=2, ensure_ascii=False))
