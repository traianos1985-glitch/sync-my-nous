"""Dashboard API — τα endpoints που καλεί το web dashboard.

Το frontend (`src/routes/dashboard.tsx`) τα καλεί όλα μέσω `nousFetch`,
δηλαδή με ένα μόνο κλειδί: το NOUS token (το guard του `auth_guard.py`
τα καλύπτει όλα, αφού είναι `before_request`).

Κάθε response έχει ακριβώς το shape που περιμένει το UI, και τα δεδομένα
έρχονται από τα πραγματικά stores του backend (queue, missions, journal,
document uploads, feedback). Όπου δεν υπάρχει ακόμη κάτι καταγεγραμμένο,
επιστρέφονται κενές λίστες / μηδενικά — ποτέ επινενοημένα δεδομένα.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from executor.agent_journal import list_journal
from executor.mission_system import (
    approve_task,
    list_missions,
    pending_approvals,
    reject_task,
    run_next_mission_task,
)
from executor.task_queue import list_queue, update_task
from executor.upload_processing_engine import UPLOADS, process_uploaded_file

dashboard_api_bp = Blueprint("dashboard_api", __name__, url_prefix="/api")

FEEDBACK_FILE = Path("data/feedback.json")
_UPLOAD_PREFIX = re.compile(r"^\d{8}_\d{6}_")
_TRUTHY = {"1", "true", "yes", "on"}


# ---------------------------------------------------------------- helpers

def _iso(value) -> str:
    """Epoch ή ISO τιμή -> ISO string. Κενό αν δεν υπάρχει (ποτέ fake date)."""
    if value in (None, ""):
        return ""
    if isinstance(value, bool):
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    return str(value)


def _journal_events(limit: int = 10, days: int | None = None, needle: str | None = None) -> list[dict]:
    items = list_journal(limit=500)
    cutoff = time.time() - days * 86400 if days else None
    events: list[dict] = []

    for item in reversed(items):
        timestamp = float(item.get("time") or 0)
        if cutoff is not None and timestamp < cutoff:
            continue
        name = str(item.get("event") or "")
        if needle and needle.lower() not in name.lower():
            continue
        data = item.get("data") or {}
        events.append(
            {
                "id": str(item.get("id")),
                "event": name,
                "createdAt": _iso(timestamp),
                "tool": data.get("tool") or data.get("action") or None,
            }
        )
        if len(events) >= limit:
            break

    return events


def _load_feedback() -> list[dict]:
    if not FEEDBACK_FILE.exists():
        return []
    try:
        return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _save_feedback(items: list[dict]) -> None:
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = FEEDBACK_FILE.with_suffix(".json.tmp")
    temp.write_text(json.dumps(items[-500:], ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(FEEDBACK_FILE)


def _split_approval(approval_id: str) -> tuple[str, str]:
    mission_id, _, task_id = str(approval_id or "").partition(":")
    return mission_id.strip(), task_id.strip()


def _map_job(item: dict) -> dict:
    return {
        "id": str(item.get("id")),
        "kind": item.get("kind") or "general",
        "status": item.get("status") or "pending",
        "retryCount": int(item.get("attempts") or 0),
        "lastError": item.get("last_error"),
        "createdAt": _iso(item.get("created")),
        "completedAt": _iso(item.get("finished")) or None,
    }


# ---------------------------------------------------------------- status

@dashboard_api_bp.get("/status")
def api_status():
    """Γενική κατάσταση: πλήθος missions + εκτελεσμένα tasks + πρόσφατα events."""
    queue = list_queue()
    finished = [q for q in queue if q.get("status") in {"done", "running", "failed"}]
    return jsonify(
        {
            "ok": True,
            "service": "nous",
            "status": "online",
            "counts": {"missions": len(list_missions()), "toolRuns": len(finished)},
            "recentEvents": _journal_events(limit=10),
        }
    )


# ---------------------------------------------------------------- knowledge

@dashboard_api_bp.get("/knowledge")
def api_knowledge_list():
    documents = []
    if UPLOADS.exists():
        files = [p for p in UPLOADS.iterdir() if p.is_file()]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for path in files:
            original = _UPLOAD_PREFIX.sub("", path.name)
            documents.append(
                {
                    "id": path.name,
                    "originalName": original,
                    "contentType": mimetypes.guess_type(original)[0] or "application/octet-stream",
                    "status": "stored",
                    "sizeBytes": path.stat().st_size,
                }
            )
    return jsonify({"ok": True, "documents": documents})


@dashboard_api_bp.post("/knowledge")
def api_knowledge_upload():
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({"ok": False, "error": "missing_file"}), 400

    suffix = Path(upload.filename).suffix
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        upload.save(handle)
        handle.close()
        result = process_uploaded_file(handle.name, original_name=upload.filename)
    finally:
        try:
            os.unlink(handle.name)
        except OSError:
            pass

    stored = result.get("stored_upload")
    if not stored:
        return jsonify({"ok": False, "error": result.get("error", "upload_failed")}), 500

    indexed = bool(result.get("ok"))
    path = Path(stored)
    return (
        jsonify(
            {
                "ok": True,
                "indexed": indexed,
                "answer": result.get("answer"),
                "document": {
                    "id": path.name,
                    "originalName": result.get("original_name") or path.name,
                    "contentType": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                    "status": "indexed" if indexed else "stored",
                    "sizeBytes": path.stat().st_size if path.exists() else 0,
                },
            }
        ),
        201,
    )


# ---------------------------------------------------------------- evaluation + feedback

@dashboard_api_bp.get("/evaluation")
def api_evaluation():
    """Metrics από τα πραγματικά ratings που στέλνει το UI (αρχικά μηδενικά)."""
    metrics = {"total": 0, "positive": 0, "negative": 0, "satisfactionRate": None, "trend": []}
    buckets: dict[str, dict] = {}
    positive = negative = 0

    for item in _load_feedback():
        rating = item.get("rating")
        timestamp = float(item.get("time") or 0)
        day = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d") if timestamp else "unknown"
        bucket = buckets.setdefault(day, {"day": day, "positive": 0, "negative": 0})
        if rating == "positive":
            positive += 1
            bucket["positive"] += 1
        elif rating == "negative":
            negative += 1
            bucket["negative"] += 1

    total = positive + negative
    metrics.update(
        {
            "total": total,
            "positive": positive,
            "negative": negative,
            "satisfactionRate": round(positive / total, 4) if total else None,
            "trend": sorted(buckets.values(), key=lambda point: point["day"])[-14:],
        }
    )
    return jsonify({"ok": True, "metrics": metrics})


@dashboard_api_bp.post("/feedback")
def api_feedback():
    data = request.get_json(silent=True) or {}
    rating = data.get("rating")
    message_id = data.get("messageId")
    if rating not in {"positive", "negative"} or not message_id:
        return jsonify({"ok": False, "error": "invalid_feedback"}), 400

    items = _load_feedback()
    items.append({"messageId": str(message_id), "rating": rating, "time": time.time()})
    _save_feedback(items)
    return jsonify({"ok": True}), 201


# ---------------------------------------------------------------- audit

@dashboard_api_bp.get("/audit")
def api_audit():
    days_raw = request.args.get("days", "30")
    try:
        days = max(1, min(int(days_raw), 365))
    except (TypeError, ValueError):
        days = 30
    needle = (request.args.get("event") or "").strip() or None
    return jsonify({"ok": True, "events": _journal_events(limit=200, days=days, needle=needle)})


# ---------------------------------------------------------------- jobs (task queue)

@dashboard_api_bp.get("/jobs")
def api_jobs():
    limit_raw = request.args.get("limit", "20")
    try:
        limit = max(1, min(int(limit_raw), 200))
    except (TypeError, ValueError):
        limit = 20

    items = sorted(list_queue(), key=lambda item: float(item.get("created") or 0), reverse=True)
    return jsonify({"ok": True, "jobs": [_map_job(item) for item in items[:limit]]})


@dashboard_api_bp.patch("/jobs")
def api_job_update():
    data = request.get_json(silent=True) or {}
    job_id = data.get("id")
    action = data.get("action")
    if not job_id or action not in {"cancel", "retry"}:
        return jsonify({"ok": False, "error": "invalid_request"}), 400

    if action == "cancel":
        item = update_task(job_id, status="cancelled", finished=time.time())
    else:
        item = update_task(job_id, status="pending", last_error=None, finished=None)

    if not item:
        return jsonify({"ok": False, "error": "job_not_found"}), 404
    return jsonify({"ok": True, "job": _map_job(item)})


# ---------------------------------------------------------------- approvals + tool execution

@dashboard_api_bp.get("/approvals")
def api_approvals():
    pending = pending_approvals().get("approvals", [])
    approvals = []
    for item in pending:
        mission_id = str(item.get("mission_id"))
        task_id = str(item.get("task_id"))
        approvals.append(
            {
                "id": f"{mission_id}:{task_id}",
                "tool": item.get("action") or item.get("task_title") or "mission_task",
                "input": {
                    "mission_id": item.get("mission_id"),
                    "mission_title": item.get("mission_title"),
                    "task_id": item.get("task_id"),
                    "task_title": item.get("task_title"),
                    "action": item.get("action"),
                },
                "createdAt": _iso(item.get("created")),
            }
        )
    return jsonify({"ok": True, "approvals": approvals, "count": len(approvals)})


@dashboard_api_bp.patch("/approvals")
def api_approval_resolve():
    data = request.get_json(silent=True) or {}
    mission_id, task_id = _split_approval(data.get("id"))
    status = data.get("status")
    if not mission_id or not task_id:
        return jsonify({"ok": False, "error": "invalid_approval_id"}), 400

    if status == "approved":
        result = approve_task(mission_id, task_id)
    elif status == "rejected":
        result = reject_task(mission_id, task_id)
    else:
        return jsonify({"ok": False, "error": "invalid_status"}), 400

    return jsonify(result), 200 if result.get("ok") else 404


@dashboard_api_bp.post("/tools/execute")
def api_tool_execute():
    """Εκτέλεση του εγκεκριμένου task: τρέχει το επόμενο task του mission.

    Οι ενέργειες περνούν από το allowlist του `mission_system` (SAFE_TASK_ACTIONS /
    APPROVAL_REQUIRED), οπότε εδώ δεν εκτελείται τίποτα εκτός εγκρίσεων.
    """
    data = request.get_json(silent=True) or {}
    mission_id, _ = _split_approval(data.get("approvalId"))
    if not mission_id:
        return jsonify({"ok": False, "error": "invalid_approval_id"}), 400

    result = run_next_mission_task(mission_id)
    executed = bool(result.get("ok")) and not result.get("idle")
    payload = {"ok": bool(result.get("ok")), "executed": executed, "result": result}

    # Αν δεν εκτελέστηκε τίποτα, απαντάμε με σφάλμα ώστε το UI να το δει
    # (το nousFetch σηκώνει error μόνο σε μη-2xx) και να μην «περάσει» σιωπηλά.
    if result.get("error") == "mission_not_found":
        return jsonify(payload), 404
    if not result.get("ok"):
        return jsonify(payload), 409
    return jsonify(payload)


# ---------------------------------------------------------------- security sentinel

@dashboard_api_bp.get("/security-audit")
def api_security_audit():
    """Defensive-only sentinel: ελέγχει τα controls του ίδιου του NOUS."""
    from executor.api_tokens import has_active_tokens

    findings: list[dict] = []
    token = os.environ.get("NOUS_TOKEN", "").strip()
    anonymous = os.environ.get("NOUS_ALLOW_ANONYMOUS", "").strip().lower() in _TRUTHY

    if anonymous:
        findings.append(
            {
                "id": "auth-anonymous",
                "severity": "high",
                "title": "Anonymous access enabled",
                "detail": "NOUS_ALLOW_ANONYMOUS=1 removes the token requirement for every endpoint.",
                "remediation": "Unset NOUS_ALLOW_ANONYMOUS and use a NOUS_TOKEN instead.",
            }
        )
    if not token and not has_active_tokens():
        findings.append(
            {
                "id": "auth-no-token",
                "severity": "high",
                "title": "No API token configured",
                "detail": "Without NOUS_TOKEN or a stored API token the service can only rely on network isolation.",
                "remediation": "Configure NOUS_TOKEN (or rotate a stored API token) on the service.",
            }
        )
    if current_app.debug or current_app.config.get("DEBUG"):
        findings.append(
            {
                "id": "debug-mode",
                "severity": "medium",
                "title": "Debug mode active",
                "detail": "Flask debug responses can leak internals and enable the interactive debugger.",
                "remediation": "Run the service with debug disabled in production.",
            }
        )
    if token:
        findings.append(
            {
                "id": "fail-closed-auth",
                "severity": "low",
                "title": "Fail-closed token auth enabled",
                "detail": "Every endpoint requires the NOUS token, so anonymous callers receive 401.",
                "remediation": "Keep the token rotated and stored outside source control.",
            }
        )

    high = sum(1 for finding in findings if finding["severity"] == "high")
    medium = sum(1 for finding in findings if finding["severity"] == "medium")
    score = max(0, 100 - high * 35 - medium * 15)

    return jsonify(
        {
            "ok": True,
            "mode": "defensive-only",
            "score": score,
            "findings": findings,
            "checkedAt": datetime.now(timezone.utc).isoformat(),
        }
    )
