from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_cmd(cmd: list[str]) -> dict[str, Any]:
    try:
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        return {
            "ok": p.returncode == 0,
            "code": p.returncode,
            "stdout": p.stdout[-4000:],
            "stderr": p.stderr[-4000:],
        }
    except Exception as e:
        return {"ok": False, "code": -1, "stdout": "", "stderr": repr(e)}


def count_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "invalid_json"
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        return len(data)
    return type(data).__name__


def run_project_health_snapshot() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)

    tracked = [
        "missions.json",
        "mission_proposals.json",
        "repair_proposals.json",
        "patch_proposals.json",
        "pending_reviews.json",
        "memory.json",
        "lessons_learned.json",
        "knowledge_queue.json",
        "decision_memory.json",
        "deep_code_analysis.json",
    ]

    counts = {name: count_json(DATA / name) for name in tracked}

    compile_check = run_cmd([
        "python", "-m", "py_compile",
        "executor/executive_loop_v4.py",
        "executor/smart_garbage_collector.py",
        "executor/self_maintenance_engine.py",
        "executor/patch_pipeline_manager.py",
        "executor/patch_proposal_enricher.py",
        "executor/mission_lifecycle_manager.py",
        "executor/review_inbox_manager.py",
        "executor/project_health_snapshot.py",
    ])

    git_status = run_cmd(["git", "status", "--short"])

    report = {
        "tool": "Project Health Snapshot",
        "timestamp": now_iso(),
        "counts": counts,
        "compile_ok": compile_check.get("ok"),
        "compile": compile_check,
        "git_status": git_status,
        "ok": bool(compile_check.get("ok")),
    }

    report_path = REPORTS / f"project_health_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


if __name__ == "__main__":
    print(json.dumps(run_project_health_snapshot(), indent=2, ensure_ascii=False))
