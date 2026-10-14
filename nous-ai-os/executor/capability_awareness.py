"""Build human-readable capability / tool awareness text for chat.

Also bridges safe tools and approval-gated tools into the chat path.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


CATEGORY_LABELS_EL = {
    "utility": "Χρήσιμα (υπολογισμοί, μονάδες, ώρα)",
    "text": "Κείμενο",
    "data": "Δεδομένα / JSON / hashes",
    "research": "Έρευνα & internet",
    "memory": "Μνήμη",
    "planning": "Σχεδιασμός / goals / tasks",
    "agent": "Agents & ομάδες",
    "plugins": "Plugins",
    "system": "Σύστημα",
    "development": "Ανάπτυξη / git / apps",
    "reasoning": "Σκέψη / αποφάσεις",
    "automation": "Αυτοματισμοί / schedules / autonomy",
    "android": "Android companion",
}


def _format_tool_result(result: Any) -> str:
    if result is None:
        return "Ολοκληρώθηκε (χωρίς λεπτομέρειες)."
    if isinstance(result, str):
        return result[:2000]
    if isinstance(result, dict):
        if result.get("answer"):
            return str(result["answer"])[:2000]
        if result.get("output"):
            return str(result["output"])[:2000]
        if result.get("error"):
            return f"Σφάλμα: {result.get('error')}"
        try:
            import json

            return json.dumps(result, ensure_ascii=False, indent=2)[:2000]
        except Exception:
            return str(result)[:2000]
    if isinstance(result, (list, tuple)):
        return "\n".join(str(x) for x in result[:30])[:2000]
    return str(result)[:2000]


def format_tool_error(action: str, exc: Exception | str | None = None, *, code: str | None = None) -> str:
    base = f"Δεν μπόρεσα να ολοκληρώσω την ενέργεια `{action}`."
    if code:
        base += f" (κωδικός: {code})"
    if exc:
        detail = str(exc).strip()
        if detail and detail not in base:
            base += f"\nΛεπτομέρεια: {detail[:400]}"
    base += "\nΔοκίμασε ξανά ή πες «τι εργαλεία έχεις;» για εναλλακτικές."
    return base


def build_capabilities_text(detailed: bool = False) -> str:
    lines: list[str] = [
        "**Τι μπορώ να κάνω (πραγματικό inventory του ΝΟΥΣ)**",
        "",
        "### Από φυσική γλώσσα στο chat",
        "• Συζήτηση, κατάσταση / έλεγχος υγείας",
        "• Αποστολές & στόχοι (λίστα + δημιουργία)",
        "• Μνήμη / search / URL / evolve / autonomous",
        "• Κατάλογος εργαλείων & ασφαλή tools",
        "• Privileged tools → approval, μετά «ενέκρινε και εκτέλεσε <id>»",
        "",
    ]
    try:
        from executor.chat_capabilities import chat_capabilities

        c = chat_capabilities()
        chat, docs, imgs = c.get("chat") or {}, c.get("documents") or {}, c.get("images") or {}
        lines.extend(
            [
                "### Chat / έγγραφα",
                f"• search={chat.get('internet_search')} url={chat.get('url_reader')} pdf={docs.get('pdf_text_extraction')} ocr={imgs.get('tesseract_binary')}",
                "",
            ]
        )
    except Exception:
        pass
    try:
        from executor.tool_catalog import tool_catalog

        catalog = tool_catalog()
        tools = catalog.get("tools") or []
        by_cat: dict[str, list[dict]] = defaultdict(list)
        for t in tools:
            if isinstance(t, dict):
                by_cat[str(t.get("category") or "other")].append(t)
        lines.append(f"### Εργαλεία: **{catalog.get('count', len(tools))}**")
        for cat in sorted(by_cat.keys()):
            items = by_cat[cat]
            label = CATEGORY_LABELS_EL.get(cat, cat)
            lines.append(f"**{label}** ({len(items)})")
            show = items if detailed else items[:5]
            for t in show:
                flag = " 🔒" if t.get("approval_required") is True else ""
                lines.append(f"  • `{t.get('name')}`{flag} — {(t.get('description') or '')[:80]}")
            if not detailed and len(items) > 5:
                lines.append(f"  • … +{len(items)-5}")
            lines.append("")
        lines.append("🔒 = approval. Μετά: «ενέκρινε και εκτέλεσε <id>».")
    except Exception as exc:
        lines.append(f"_tool_catalog error: {exc}_")
    return "\n".join(lines).strip()


def build_tools_list_text(category: str | None = None) -> str:
    try:
        from executor.tool_catalog import tool_catalog

        catalog = tool_catalog(category=category)
    except Exception as exc:
        return format_tool_error("tool_catalog", exc)
    tools = catalog.get("tools") or []
    if not tools:
        return "Δεν βρήκα εργαλεία για αυτή την κατηγορία."
    lines = [f"**Εργαλεία** ({catalog.get('count', len(tools))})", ""]
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for t in tools:
        if isinstance(t, dict):
            by_cat[str(t.get("category") or "other")].append(t)
    for cat in sorted(by_cat.keys()):
        lines.append(f"### {CATEGORY_LABELS_EL.get(cat, cat)}")
        for t in by_cat[cat]:
            appr = " 🔒" if t.get("approval_required") is True else ""
            lines.append(f"• **{t.get('name')}**{appr} — {t.get('description', '')}")
            lines.append(f"  `{t.get('command') or t.get('name')}`")
        lines.append("")
    return "\n".join(lines).strip()


SAFE_CHAT_TOOLS = {
    "tool_catalog", "calculate", "convert", "time", "text_stats", "json_validate", "json_format",
    "sha256", "url_encode", "url_decode", "sysinfo", "snapshot", "compile", "git_status",
    "daily_brief", "list_schedules", "memory_summary", "personal_state", "tasks", "list_apps",
    "plugin", "action_log", "next_action", "repair_advice", "autonomy_status", "cloud_info", "agent_review",
}

PRIVILEGED_CHAT_TOOLS = {
    "make_plugin", "forge_plugin", "run_plugin", "test_plugin", "quarantine_plugin", "make_app",
    "repair_system", "autonomy_start", "autonomy_cycle", "clear_schedules", "agent_solve",
    "agent_checkpoint", "team_plan", "team_solve", "notify", "git_checkpoint",
}

_RATE: dict[str, float] = {}
_RATE_MIN_INTERVAL = 2.0


def allow_external_call(key: str = "external") -> tuple[bool, str]:
    import time

    now = time.time()
    last = _RATE.get(key, 0.0)
    if now - last < _RATE_MIN_INTERVAL:
        wait = _RATE_MIN_INTERVAL - (now - last)
        return False, f"Περίμενε ~{wait:.1f}s πριν την επόμενη εξωτερική κλήση (rate limit)."
    _RATE[key] = now
    return True, ""


def run_safe_tool(action: str, command: str = "") -> dict[str, Any]:
    action = (action or "").strip()
    if action not in SAFE_CHAT_TOOLS:
        return {"ok": False, "error": "tool_not_safe_for_chat", "answer": format_tool_error(action, code="not_safe")}
    try:
        from executor.tools import run_tool

        result = run_tool({"action": action}, {"command": command or action})
    except Exception as exc:
        return {"ok": False, "error": str(exc), "answer": format_tool_error(action, exc)}
    if result == "UNKNOWN TOOL":
        return {"ok": False, "error": "unknown_tool", "answer": format_tool_error(action, code="unknown_tool")}
    return {"ok": True, "result": result, "answer": _format_tool_result(result)}


def request_privileged_tool(action: str, command: str = "", reason: str | None = None) -> dict[str, Any]:
    action = (action or "").strip()
    if action not in PRIVILEGED_CHAT_TOOLS:
        try:
            from executor.tool_catalog import get_tool

            meta = get_tool(action) or {}
            if meta.get("approval_required") is not True:
                return {"ok": False, "error": "not_privileged", "answer": format_tool_error(action, code="not_privileged")}
        except Exception:
            return {"ok": False, "error": "unknown_tool", "answer": format_tool_error(action, code="unknown_tool")}

    payload = {"tool": action, "command": command or action, "source": "chat_nl"}
    reason = reason or f"Chat ζήτησε privileged tool: {action}"
    try:
        from executor.operator_approval import request_approval

        approval = request_approval(action, payload, reason)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "answer": format_tool_error(action, exc)}

    aid = approval.get("id") if isinstance(approval, dict) else None
    text = (
        f"🔒 Το **`{action}`** απαιτεί έγκριση.\n\n"
        f"Αίτημα" + (f" id `{aid}`" if aid is not None else "") + ".\n"
        f"Εντολή: `{command or action}`\n\n"
        f"Πες **ενέκρινε και εκτέλεσε {aid}** στο chat ή ενέκρινε από dashboard."
    )
    return {
        "ok": True,
        "approval_required": True,
        "approval_id": str(aid) if aid is not None else None,
        "action": action,
        "command": command or action,
        "approval": approval,
        "answer": text,
    }


def list_pending_approvals_text() -> str:
    try:
        from executor.operator_approval import list_approvals

        items = list_approvals(status="pending") or []
    except Exception as exc:
        return format_tool_error("list_approvals", exc)
    if not items:
        return "Δεν υπάρχουν εκκρεμείς εγκρίσεις."
    lines = ["**Εκκρεμείς εγκρίσεις:**", ""]
    for item in items[:20]:
        aid, action = item.get("id"), item.get("action")
        lines.append(f"• id `{aid}` — **{action}**")
        payload = item.get("payload") or {}
        if isinstance(payload, dict) and payload.get("command"):
            lines.append(f"  `{payload.get('command')}`")
    lines.append("\n«ενέκρινε και εκτέλεσε <id>» · «απέρριψε approval <id>»")
    return "\n".join(lines)


def approve_and_execute(approval_id: str) -> dict[str, Any]:
    from executor.operator_approval import approve, claim_approved_approval, finish_approval, get_approval
    from executor.tools import run_tool

    item = get_approval(approval_id)
    if not item:
        return {"ok": False, "error": "not_found", "answer": format_tool_error("approve", code="approval_not_found")}

    status = item.get("status")
    action = str(item.get("action") or "")
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}

    if status == "pending":
        approved = approve(approval_id)
        if not approved:
            return {"ok": False, "error": "approve_failed", "answer": format_tool_error(action or "approve", code="approve_failed")}
        item, status = approved, approved.get("status")

    if status != "approved":
        return {"ok": False, "error": f"bad_status_{status}", "answer": f"Approval `{approval_id}` σε κατάσταση **{status}**."}

    claimed = claim_approved_approval(approval_id, action, payload)
    if not claimed:
        return {"ok": False, "error": "claim_failed", "answer": format_tool_error(action, code="claim_failed")}

    command = str(payload.get("command") or action)
    try:
        result = run_tool({"action": action}, {"command": command})
        ok = result != "UNKNOWN TOOL" and not (isinstance(result, dict) and result.get("ok") is False and result.get("error"))
        finish_approval(
            approval_id,
            "completed" if ok else "failed",
            result if isinstance(result, dict) else {"result": result},
        )
        text = _format_tool_result(result)
        if not ok:
            text = format_tool_error(action, code="tool_failed") + "\n\n" + text
        return {
            "ok": bool(ok),
            "approval_id": str(approval_id),
            "action": action,
            "result": result,
            "answer": f"✅ Εκτέλεσα `{action}` (approval `{approval_id}`).\n\n{text}",
        }
    except Exception as exc:
        try:
            finish_approval(approval_id, "failed", {"error": str(exc)})
        except Exception:
            pass
        return {"ok": False, "error": str(exc), "answer": format_tool_error(action, exc)}


def reject_approval_request(approval_id: str) -> dict[str, Any]:
    try:
        from executor.operator_approval import reject

        item = reject(approval_id)
    except Exception as exc:
        return {"ok": False, "answer": format_tool_error("reject", exc)}
    if not item:
        return {"ok": False, "answer": f"Δεν μπόρεσα να απορρίψω το approval `{approval_id}`."}
    return {"ok": True, "answer": f"✅ Απέρριψα approval `{approval_id}` ({item.get('action')}).", "approval": item}
