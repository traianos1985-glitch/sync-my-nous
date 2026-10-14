"""Build human-readable capability / tool awareness text for chat."""

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
        # compact json-ish summary
        try:
            import json

            return json.dumps(result, ensure_ascii=False, indent=2)[:2000]
        except Exception:
            return str(result)[:2000]
    if isinstance(result, (list, tuple)):
        return "\n".join(str(x) for x in result[:30])[:2000]
    return str(result)[:2000]


def build_capabilities_text(detailed: bool = False) -> str:
    """Full self-awareness blurb for «τι μπορείς» / capabilities."""
    lines: list[str] = [
        "**Τι μπορώ να κάνω (πραγματικό inventory του ΝΟΥΣ)**",
        "",
        "### Από φυσική γλώσσα στο chat",
        "• Συζήτηση, κατάσταση / έλεγχος υγείας",
        "• Αποστολές & στόχοι (λίστα + δημιουργία)",
        "• Μνήμη («θυμάσαι…»)",
        "• Αναζήτηση internet & βαθιά έρευνα",
        "• Ανάγνωση URL («διάβασε https://…»)",
        "• Εξέλιξη (status, χωρίς auto-patch από chat)",
        "• Αυτόνομη λειτουργία (ξεκίνα / σταμάτα / κατάσταση)",
        "• Κατάλογος εργαλείων («τι εργαλεία έχεις;» / «tools»)",
        "",
    ]

    # Chat document / OCR capabilities
    try:
        from executor.chat_capabilities import chat_capabilities

        c = chat_capabilities()
        chat = c.get("chat") or {}
        docs = c.get("documents") or {}
        imgs = c.get("images") or {}
        lines.extend(
            [
                "### Chat / έγγραφα / εικόνες",
                f"• Internet search module: {chat.get('internet_search')}",
                f"• URL reader: {chat.get('url_reader')}",
                f"• PDF extraction: {docs.get('pdf_text_extraction')}",
                f"• DOCX extraction: {docs.get('docx_text_extraction')}",
                f"• OCR (tesseract binary): {imgs.get('tesseract_binary')}",
                "• Πραγματική vision κατανόηση εικόνας: όχι (OCR μόνο)",
                "",
            ]
        )
    except Exception:
        lines.append("_Δεν μπόρεσα να φορτώσω chat_capabilities._\n")

    # Tool catalog
    try:
        from executor.tool_catalog import tool_catalog

        catalog = tool_catalog()
        tools = catalog.get("tools") or []
        by_cat: dict[str, list[dict]] = defaultdict(list)
        for t in tools:
            if isinstance(t, dict):
                by_cat[str(t.get("category") or "other")].append(t)

        lines.append(f"### Καταχωρημένα εργαλεία: **{catalog.get('count', len(tools))}**")
        lines.append("")
        for cat in sorted(by_cat.keys()):
            label = CATEGORY_LABELS_EL.get(cat, cat)
            items = by_cat[cat]
            lines.append(f"**{label}** ({len(items)})")
            show = items if detailed else items[:6]
            for t in show:
                name = t.get("name", "?")
                desc = (t.get("description") or "").strip()
                risk = t.get("risk") or ""
                appr = t.get("approval_required")
                flag = " 🔒" if appr is True else ""
                short = desc[:90] + ("…" if len(desc) > 90 else "")
                lines.append(f"  • `{name}`{flag} — {short}")
            if not detailed and len(items) > 6:
                lines.append(f"  • … και άλλα {len(items) - 6} (πες «δείξε όλα τα εργαλεία»)")
            lines.append("")
        lines.append(
            "🔒 = απαιτεί έγκριση operator. "
            "Λεπτομέρειες: πες «τι εργαλεία έχεις;» ή «εργαλεία κατηγορίας research»."
        )
    except Exception as exc:
        lines.append(f"_Δεν μπόρεσα να φορτώσω tool_catalog: {exc}_")

    return "\n".join(lines).strip()


def build_tools_list_text(category: str | None = None) -> str:
    """Focused tool list answer."""
    try:
        from executor.tool_catalog import tool_catalog

        catalog = tool_catalog(category=category)
    except Exception as exc:
        return f"Δεν μπόρεσα να διαβάσω τον κατάλογο εργαλείων: {exc}"

    tools = catalog.get("tools") or []
    if not tools:
        cats = ", ".join(catalog.get("categories") or [])
        return f"Δεν βρήκα εργαλεία για αυτή την κατηγορία. Διαθέσιμες: {cats}"

    lines = [
        f"**Εργαλεία NOUS** ({catalog.get('count', len(tools))})"
        + (f" — κατηγορία `{category}`" if category else ""),
        "",
    ]
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for t in tools:
        if isinstance(t, dict):
            by_cat[str(t.get("category") or "other")].append(t)

    for cat in sorted(by_cat.keys()):
        label = CATEGORY_LABELS_EL.get(cat, cat)
        lines.append(f"### {label}")
        for t in by_cat[cat]:
            appr = " 🔒" if t.get("approval_required") is True else ""
            cmd = t.get("command") or t.get("name")
            lines.append(f"• **{t.get('name')}**{appr} — {t.get('description', '')}")
            lines.append(f"  εντολή: `{cmd}`")
        lines.append("")

    lines.append("Μπορείς να ζητήσεις π.χ. «git status», «daily brief», «schedules», «υπολόγισε 12*7».")
    return "\n".join(lines).strip()


# Safe tools callable from chat without operator approval
SAFE_CHAT_TOOLS = {
    "tool_catalog",
    "calculate",
    "convert",
    "time",
    "text_stats",
    "json_validate",
    "json_format",
    "sha256",
    "url_encode",
    "url_decode",
    "sysinfo",
    "snapshot",
    "compile",
    "git_status",
    "daily_brief",
    "list_schedules",
    "memory_summary",
    "personal_state",
    "tasks",
    "list_apps",
    "plugin",
    "action_log",
    "next_action",
    "repair_advice",
    "autonomy_status",
    "cloud_info",
    "agent_review",
}


def run_safe_tool(action: str, command: str = "") -> dict[str, Any]:
    """Execute a read-only / local tool via tools.run_tool when safe."""
    action = (action or "").strip()
    if action not in SAFE_CHAT_TOOLS:
        return {
            "ok": False,
            "error": "tool_not_safe_for_chat",
            "answer": f"Το εργαλείο `{action}` δεν εκτελείται αυτόματα από chat χωρίς έγκριση.",
        }
    try:
        from executor.tools import run_tool

        result = run_tool({"action": action}, {"command": command or action})
    except Exception as exc:
        return {"ok": False, "error": str(exc), "answer": f"Αποτυχία εκτέλεσης `{action}`: {exc}"}

    if result == "UNKNOWN TOOL":
        return {"ok": False, "error": "unknown_tool", "answer": f"Άγνωστο εργαλείο: `{action}`"}

    return {"ok": True, "result": result, "answer": _format_tool_result(result)}
