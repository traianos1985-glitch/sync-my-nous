"""Upgrade Planner — NOUS προτείνει και εκτελεί αναβαθμίσεις του εαυτού του."""
import json, os, time, threading, subprocess
from pathlib import Path

FILE = "data/upgrade_plans.json"

_COOLDOWN_DAYS = 30  # μη ξαναπροτείνεις αναβάθμιση για 30 ημέρες μετά από approval


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


UPGRADES = [
    {
        "title": "True Patch Generator",
        "priority": 1,
        "reason": "Turns code analysis into concrete diffs.",
        "modules": ["deep_code_analyst", "patch_generator", "self_healing_loop"],
        "file": "executor/true_patch_generator.py",
    },
    {
        "title": "Real Code Evolution Engine",
        "priority": 2,
        "reason": "Build route/UI/service dependency graph and multi-file patches.",
        "modules": ["repository_index", "route_graph", "ui_action_graph"],
        "file": "executor/code_evolution_engine.py",
    },
    {
        "title": "Cloud Brain Sync",
        "priority": 3,
        "reason": "Protects the brain from device loss.",
        "modules": ["brain_backup", "cloud_sync", "restore_verify"],
        "file": "executor/cloud_brain_sync.py",
    },
    {
        "title": "Approval Center Actions",
        "priority": 4,
        "reason": "Approve/reject directly from Pending Inbox.",
        "modules": ["pending_review", "approval_router", "ui_buttons"],
        "file": "executor/approval_center.py",
    },
]


def propose_upgrade_plan():
    items = _load()
    # Don't propose if a plan is pending or was recently approved/implemented/rejected
    cutoff = time.time() - _COOLDOWN_DAYS * 86400
    for x in items:
        if x.get("status") == "pending":
            return {"ok": True, "deduped": True, "plan": x}
        if x.get("status") in ("approved", "implementing", "implemented", "rejected"):
            ts = x.get("approved") or x.get("rejected") or x.get("created", 0)
            if ts > cutoff:
                return {"ok": True, "deduped": True, "plan": x, "reason": "recent"}

    plan = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "status": "pending",
        "title": "NOUS Next Upgrade Plan",
        "upgrades": UPGRADES,
        "execution_log": [],
    }
    items.append(plan)
    _save(items)
    return {"ok": True, "plan": plan}


def upgrade_planner_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "pending": len([x for x in items if x.get("status") == "pending"]),
        "plans": items[-20:],
    }


def list_upgrade_plans(limit=20):
    return _load()[-int(limit):]


def approve_upgrade_plan(plan_id):
    items = _load()
    for p in items:
        if str(p.get("id")) == str(plan_id):
            p["status"] = "implementing"
            p["approved"] = time.time()
            p["execution_log"] = ["⏳ Εγκρίθηκε — ξεκινά η αυτόματη υλοποίηση…"]
            _save(items)
            # Run actual implementation in background
            t = threading.Thread(target=_execute_upgrade_plan, args=(dict(p),), daemon=True)
            t.start()
            return {"ok": True, "plan": p}
    return {"ok": False, "error": "plan_not_found"}


def _execute_upgrade_plan(plan: dict):
    """Εκτελεί πραγματικά την αναβάθμιση — γράφει κώδικα για κάθε module."""
    plan_id = str(plan["id"])
    log = list(plan.get("execution_log", []))

    def _append(msg: str):
        log.append(msg)
        items = _load()
        for p in items:
            if str(p.get("id")) == plan_id:
                p["execution_log"] = list(log)
                break
        _save(items)

    try:
        upgrades_done = []
        for upgrade in plan.get("upgrades", []):
            title   = upgrade.get("title", "")
            modules = upgrade.get("modules", [])
            fpath   = upgrade.get("file", f"executor/upgrade_{title.lower().replace(' ','_')}.py")

            _append(f"🔧 Υλοποίηση: {title}…")

            if Path(fpath).exists():
                _append(f"  ✅ {title} — αρχείο υπάρχει ({fpath})")
                upgrades_done.append(title)
                continue

            # Generate via LLM
            try:
                from executor.remote_llm import ask
                code = ask(
                    f"Γράψε ένα Python module για: {title}\n"
                    f"Λόγος: {upgrade.get('reason','')}\n"
                    f"Modules που αποτελεί: {', '.join(modules)}\n"
                    "Απαιτήσεις:\n"
                    "- Χρησιμοποίησε μόνο standard library + requests + pathlib\n"
                    "- Πρόσθεσε status() function που επιστρέφει dict\n"
                    "- Γράψε ΜΟΝΟ Python κώδικα, χωρίς markdown ή εξηγήσεις",
                    system=(
                        "Είσαι expert Python/Flask developer. "
                        "Γράψε ΜΟΝΟ Python code — χωρίς markdown, χωρίς ```python, χωρίς εξηγήσεις."
                    )
                )
                # Strip markdown fences
                code = "\n".join(l for l in code.splitlines() if not l.strip().startswith("```"))
                if code and len(code) > 50:
                    Path(fpath).write_text(code, encoding="utf-8")
                    # Validate
                    r = subprocess.run(["python", "-m", "py_compile", fpath],
                                       capture_output=True, text=True, timeout=15)
                    if r.returncode == 0:
                        _append(f"  ✅ {title} — κώδικας γράφτηκε στο {fpath}")
                        upgrades_done.append(title)
                    else:
                        _append(f"  ⚠️ {title} — σφάλμα σύνταξης: {r.stderr[:80]}")
                else:
                    _append(f"  ⚠️ {title} — LLM δεν παρήγαγε αξιόπιστο κώδικα")
            except Exception as e:
                _append(f"  ⚠️ {title} — error: {e}")

        summary = f"Υλοποιήθηκαν {len(upgrades_done)}/{len(plan.get('upgrades',[]))} modules: {', '.join(upgrades_done)}"
        _append(f"✅ Αναβάθμιση ολοκληρώθηκε! {summary}")

        items = _load()
        for p in items:
            if str(p.get("id")) == plan_id:
                p["status"] = "implemented"
                p["implemented"] = time.time()
                p["execution_log"] = list(log)
                p["result"] = summary
                break
        _save(items)

    except Exception as e:
        _append(f"❌ Σφάλμα αναβάθμισης: {e}")
        items = _load()
        for p in items:
            if str(p.get("id")) == plan_id:
                p["status"] = "failed"
                p["execution_log"] = list(log)
                break
        _save(items)


def get_plan(plan_id: str) -> dict | None:
    for p in _load():
        if str(p.get("id")) == str(plan_id):
            return p
    return None


def reject_upgrade_plan(plan_id, reason="User rejected upgrade plan"):
    items = _load()
    for p in items:
        if str(p.get("id")) == str(plan_id):
            p["status"] = "rejected"
            p["rejected"] = time.time()
            p["reject_reason"] = reason
            _save(items)
            return {"ok": True, "plan": p}
    return {"ok": False, "error": "plan_not_found"}
