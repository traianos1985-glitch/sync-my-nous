import json
import os
import subprocess
import time

REPORT_FILE = "data/self_diagnosis_report.json"

CHECK_FILES = [
    "executor/router.py",
    "executor/nous_ui.py",
    "executor/mission_system.py",
    "executor/mission_planner.py",
    "executor/dashboard_action_audit.py",
    "executor/executive_intelligence.py",
    "executor/executive_scheduler_loop.py",
    "executor/goal_progress_intelligence.py",
]


def _run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {"ok": p.returncode == 0, "code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _save(report):
    os.makedirs("data", exist_ok=True)
    json.dump(report, open(REPORT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def self_diagnosis_status():
    if not os.path.exists(REPORT_FILE):
        return {"ok": True, "exists": False, "message": "No self diagnosis report yet."}
    try:
        return {"ok": True, "exists": True, "report": json.load(open(REPORT_FILE, "r", encoding="utf-8"))}
    except Exception as e:
        return {"ok": False, "exists": True, "error": str(e)}


def run_self_diagnosis():
    report = {
        "ok": True,
        "time": time.time(),
        "checks": {},
        "problems": [],
        "recommended_fixes": [],
    }

    compile_results = {}
    for f in CHECK_FILES:
        if os.path.exists(f):
            r = _run(["python", "-m", "py_compile", f])
            compile_results[f] = r
            if not r.get("ok"):
                report["ok"] = False
                report["problems"].append({"type": "compile_error", "file": f, "result": r})
        else:
            report["problems"].append({"type": "missing_file", "file": f})

    report["checks"]["compile"] = compile_results

    try:
        from executor.router import app
        client = app.test_client()

        endpoints = [
            "/dashboard",
            "/remote/status",
            "/remote/dashboard-action-audit",
            "/remote/mission-planner/status",
            "/remote/executive-intelligence/status",
            "/remote/executive-scheduler-loop/status",
            "/remote/goal-progress-intelligence/status",
        ]

        endpoint_results = []
        for path in endpoints:
            r = client.get(path)
            ok = r.status_code < 400
            endpoint_results.append({"path": path, "status": r.status_code, "ok": ok, "json": r.is_json})
            if not ok:
                report["ok"] = False
                report["problems"].append({"type": "endpoint_failed", "path": path, "status": r.status_code})

        report["checks"]["endpoints"] = endpoint_results

        audit = client.get("/remote/dashboard-action-audit")
        if audit.is_json:
            data = audit.get_json()
            report["checks"]["dashboard_action_audit"] = data
            failed = [x for x in data.get("results", []) if not x.get("ok")]
            if failed:
                report["ok"] = False
                report["problems"].append({"type": "dashboard_action_failures", "failed": failed})
                report["recommended_fixes"].append({
                    "id": "dashboard_auth_helpers",
                    "title": "Repair dashboard auth/error helpers",
                    "risk": "low",
                    "description": "Reinstall central getJson/postJson auth helpers and error reporting."
                })
        else:
            report["problems"].append({"type": "audit_not_json"})

    except Exception as e:
        report["ok"] = False
        report["problems"].append({"type": "self_diagnosis_exception", "error": str(e)})

    git = _run(["git", "status", "--short"])
    report["checks"]["git_status"] = git

    if git.get("stdout"):
        report["recommended_fixes"].append({
            "id": "review_runtime_files",
            "title": "Review runtime file changes",
            "risk": "manual",
            "description": "Runtime files changed. User should decide restore or commit."
        })

    _save(report)
    return report


def apply_safe_self_fix(fix_id):
    if fix_id == "dashboard_auth_helpers":
        from pathlib import Path
        import re

        p = Path("executor/nous_ui.py")
        s = p.read_text()

        helpers = r'''
function getToken(){
  return localStorage.getItem("NOUS_TOKEN") || "";
}

function authHeaders(extra){
  const t = getToken();
  const h = Object.assign({"Content-Type":"application/json"}, extra || {});
  if(t){
    h["X-NOUS-Token"] = t;
    h["Authorization"] = "Bearer " + t;
  }
  return h;
}

async function getJson(url){
  const r = await fetch(url, {headers: authHeaders({})});
  const data = await r.json().catch(()=>({error:"invalid_json"}));
  if(!r.ok){
    const err = {ok:false, status:r.status, error:data.error || "request_failed", url, data};
    renderObject(err);
    feed("GET failed " + r.status + " " + url);
    return err;
  }
  return data;
}

async function postJson(url, body){
  const r = await fetch(url, {
    method:"POST",
    headers: authHeaders({}),
    body: JSON.stringify(body || {})
  });
  const data = await r.json().catch(()=>({error:"invalid_json"}));
  if(!r.ok || data.error){
    const err = {ok:false, status:r.status, error:data.error || "request_failed", url, data};
    renderObject(err);
    feed("POST failed " + r.status + " " + url + " — " + err.error);
    return err;
  }
  return data;
}
'''

        pattern = r'function getToken\(\)\{.*?async function postJson\(url, body\)\{.*?\n\}'
        m = re.search(pattern, s, flags=re.S)

        if m:
            s = s[:m.start()] + helpers + s[m.end():]
        else:
            return {"ok": False, "error": "helpers_block_not_found"}

        p.write_text(s)
        compile_result = _run(["python", "-m", "py_compile", "executor/nous_ui.py"])
        return {"ok": compile_result.get("ok"), "fix_id": fix_id, "compile": compile_result}

    return {"ok": False, "error": "unknown_or_unsafe_fix", "fix_id": fix_id}
