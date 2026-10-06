"""Safety net: incident log and circuit breaker for autonomous actions."""

import json
import os
import time
from datetime import datetime, timezone

FILE = "data/safety_net.json"
FAILURE_THRESHOLD = 3
COOLDOWN_SEC = 300
MAX_INCIDENTS = 500


def _default_state():
    return {"incidents": [], "circuit": {"state": "closed", "failures": 0, "opened_at": None}}


def _load():
    if not os.path.exists(FILE):
        return _default_state()
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return _default_state()
    if not isinstance(data, dict):
        return _default_state()
    state = _default_state()
    state["incidents"] = data.get("incidents") if isinstance(data.get("incidents"), list) else []
    if isinstance(data.get("circuit"), dict):
        state["circuit"].update(data["circuit"])
    return state


def _save(state):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _circuit_view(circuit):
    view = dict(circuit)
    if circuit.get("state") == "open" and circuit.get("opened_at"):
        remaining = int(circuit["opened_at"] + COOLDOWN_SEC - time.time())
        if remaining <= 0:
            view["state"] = "half_open"
            remaining = 0
        view["cooldown_remaining_sec"] = remaining
    return view


def record_incident(action, outcome, files=None, error=None, backup_ids=None):
    state = _load()
    now = time.time()
    incident = {
        "id": str(time.time_ns()),
        "ts": now,
        "iso": datetime.fromtimestamp(now, timezone.utc).isoformat(),
        "action": action,
        "outcome": outcome,
        "files": list(files or []),
        "error": error,
        "backup_ids": list(backup_ids or []),
        "rolled_back": False,
    }
    circuit = state["circuit"]
    if outcome == "success":
        circuit.update({"state": "closed", "failures": 0, "opened_at": None})
    elif outcome == "failure":
        circuit["failures"] = int(circuit.get("failures") or 0) + 1
        if circuit["failures"] >= FAILURE_THRESHOLD:
            circuit.update({"state": "open", "opened_at": now})
    state["incidents"] = (state["incidents"] + [incident])[-MAX_INCIDENTS:]
    _save(state)
    return incident


def allows_action():
    return _circuit_view(_load()["circuit"]).get("state") != "open"


def list_incidents(limit=40):
    limit = max(1, min(int(limit), MAX_INCIDENTS))
    return list(reversed(_load()["incidents"]))[:limit]


def safety_status():
    state = _load()
    incidents = state["incidents"]
    circuit = _circuit_view(state["circuit"])
    summary = {
        "total": len(incidents),
        "successes": sum(1 for i in incidents if i.get("outcome") == "success"),
        "failures": sum(1 for i in incidents if i.get("outcome") == "failure"),
        "blocked": sum(1 for i in incidents if i.get("outcome") == "blocked"),
        "rollbacks": sum(1 for i in incidents if i.get("rolled_back")),
        "circuit": circuit,
    }
    return {
        "ok": True,
        "summary": summary,
        "circuit": circuit,
        "recent_incidents": list(reversed(incidents))[:20],
    }


def reset_circuit():
    state = _load()
    state["circuit"] = {"state": "closed", "failures": 0, "opened_at": None}
    _save(state)
    return {"ok": True, "circuit": state["circuit"]}


def manual_rollback(incident_id):
    from executor.rollback_engine import rollback_backup

    state = _load()
    incident = next((i for i in state["incidents"] if str(i.get("id")) == str(incident_id)), None)
    if not incident:
        return {"ok": False, "error": "incident_not_found"}
    if incident.get("rolled_back"):
        return {"ok": False, "error": "already_rolled_back"}
    backup_ids = incident.get("backup_ids") or []
    if not backup_ids:
        return {"ok": False, "error": "no_backups_for_incident"}

    results = [rollback_backup(backup_id) for backup_id in backup_ids]
    ok = all(isinstance(r, dict) and r.get("ok") for r in results)
    if ok:
        incident["rolled_back"] = True
        state["incidents"].append(
            {
                **incident,
                "id": str(time.time_ns()),
                "ts": time.time(),
                "iso": datetime.now(timezone.utc).isoformat(),
                "outcome": "rollback_manual",
                "source_incident": incident["id"],
            }
        )
        state["incidents"] = state["incidents"][-MAX_INCIDENTS:]
        _save(state)
    return {"ok": ok, "incident_id": incident_id, "results": results}
