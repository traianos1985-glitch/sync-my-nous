import difflib
import json
import os
import re
import subprocess
import time
from pathlib import Path

PROPOSAL_FILE = "data/patch_proposals.json"


def _load():
    if not os.path.exists(PROPOSAL_FILE):
        return []
    try:
        return json.load(open(PROPOSAL_FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(PROPOSAL_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        return {"ok": p.returncode == 0, "code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _diff(path, old, new):
    return "".join(difflib.unified_diff(
        old.splitlines(True),
        new.splitlines(True),
        fromfile=path + ".before",
        tofile=path + ".after",
    ))


def _dashboard_auth_patch():
    path = "executor/nous_ui.py"
    p = Path(path)
    old = p.read_text(encoding="utf-8", errors="replace")

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
    m = re.search(pattern, old, flags=re.S)

    if not m:
        return {
            "ok": False,
            "error": "dashboard_auth_helpers_block_not_found",
            "path": path,
        }

    new = old[:m.start()] + helpers + old[m.end():]

    return {
        "ok": True,
        "path": path,
        "old": old,
        "new": new,
        "diff": _diff(path, old, new),
        "apply_strategy": "replace_file",
    }


def generate_patch_from_analysis(analysis):
    problem_text = json.dumps(analysis, ensure_ascii=False).lower()
    patches = []

    if "401" in problem_text or "unauthorized" in problem_text or "auth" in problem_text:
        p = _dashboard_auth_patch()
        if p.get("ok"):
            patches.append(p)

    proposal = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "status": "pending",
        "title": "Patch proposal from deep code analysis",
        "risk": "low" if patches else "manual",
        "analysis": analysis,
        "patches": [
            {
                "path": x.get("path"),
                "diff": x.get("diff"),
                "apply_strategy": x.get("apply_strategy"),
            }
            for x in patches
        ],
        "can_apply": bool(patches),
        "reason": "Generated concrete patch where a safe known repair pattern was found." if patches else "No safe automatic patch pattern matched. Manual review required.",
    }

    items = _load()
    items.append(proposal)
    _save(items)

    return {"ok": True, "proposal": proposal}


def list_patch_proposals(limit=50):
    return _load()[-int(limit):]


def patch_generator_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "pending": len([x for x in items if x.get("status") == "pending"]),
        "approved": len([x for x in items if x.get("status") == "approved"]),
        "rejected": len([x for x in items if x.get("status") == "rejected"]),
        "recent": items[-10:],
    }


def _find(items, proposal_id):
    for x in items:
        if str(x.get("id")) == str(proposal_id):
            return x
    return None


def approve_patch_proposal(proposal_id):
    items = _load()
    p = _find(items, proposal_id)
    if not p:
        return {"ok": False, "error": "proposal_not_found"}

    if p.get("status") != "pending":
        return {"ok": False, "error": "proposal_not_pending", "proposal": p}

    if not p.get("can_apply"):
        return {"ok": False, "error": "proposal_requires_manual_review", "proposal": p}

    applied = []

    for patch in p.get("patches", []):
        path = patch.get("path")
        if not path or patch.get("apply_strategy") != "replace_file":
            continue

        # Recreate currently supported safe patch.
        if path == "executor/nous_ui.py":
            safe = _dashboard_auth_patch()
            if not safe.get("ok"):
                p["status"] = "failed"
                p["result"] = safe
                _save(items)
                return {"ok": False, "error": "safe_patch_failed", "result": safe}

            Path(path).write_text(safe["new"], encoding="utf-8")
            applied.append(path)

    compile_results = {}
    for f in sorted(set(applied)):
        if f.endswith(".py"):
            compile_results[f] = _run(["python", "-m", "py_compile", f])

    router_compile = _run(["python", "-m", "py_compile", "executor/router.py"])
    compile_results["executor/router.py"] = router_compile

    ok = all(v.get("ok") for v in compile_results.values())

    p["status"] = "approved" if ok else "failed"
    p["approved"] = time.time()
    p["result"] = {
        "applied": applied,
        "compile": compile_results,
    }
    _save(items)

    return {"ok": ok, "proposal": p}


def reject_patch_proposal(proposal_id, reason="User rejected patch proposal"):
    items = _load()
    p = _find(items, proposal_id)
    if not p:
        return {"ok": False, "error": "proposal_not_found"}
    p["status"] = "rejected"
    p["rejected"] = time.time()
    p["reject_reason"] = reason
    _save(items)
    return {"ok": True, "proposal": p}
