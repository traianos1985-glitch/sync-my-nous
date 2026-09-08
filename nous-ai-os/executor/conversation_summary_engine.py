from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from executor.conversation_manager import get_conversation, save_json, CONV_DIR

REPORTS = Path("data/reports")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()



def is_noise_for_summary(content: str) -> bool:
    low = clean(content).lower()

    noise_parts = [
        "θυμάσαι τι",
        "θυμασαι τι",
        "τι είπα πριν",
        "τι ειπα πριν",
        "τι συζητάμε εδώ",
        "τι συζηταμε εδω",
        "στην ενεργή συνομιλία θυμάμαι",
        "στην ενεργη συνομιλια θυμαμαι",
        "από την πρόσφατη συνομιλία θυμάμαι",
        "απο την προσφατη συνομιλια θυμαμαι",
        "δεν είμαι βέβαιος για την απάντηση",
        "δεν ειμαι βεβαιος για την απαντηση",
    ]

    return any(x in low for x in noise_parts)


def looks_corrupted_summary_text(content: str) -> bool:
    low = clean(content).lower()

    bad_fragments = [
        "επιδελιώστα",
        "κραταγωγή",
        "έπληθιστε",
        "ακριηζον",
        "ηπαγωγή",
        "ναιμησίας",
        "πлавή",
    ]

    return any(x in low for x in bad_fragments)


def summarize_messages(messages: list[dict[str, Any]], max_bullets: int = 12) -> str:
    bullets = []
    seen = set()

    for m in messages:
        if not isinstance(m, dict):
            continue

        role = m.get("role")
        content = clean(m.get("content", ""))

        if not content:
            continue

        if is_noise_for_summary(content):
            continue

        if looks_corrupted_summary_text(content):
            continue

        if len(content) > 220:
            content = content[:220].rstrip() + "..."

        key = f"{role}:{content.lower()}"
        if key in seen:
            continue
        seen.add(key)

        label = "Χρήστης" if role == "user" else "ΝΟΥΣ"
        bullets.append(f"• {label}: {content}")

        if len(bullets) >= max_bullets:
            break

    if not bullets:
        return "Δεν υπάρχει ακόμα αρκετό χρήσιμο περιεχόμενο για περίληψη."

    return "Περίληψη συνομιλίας:\n\n" + "\n".join(bullets)


def update_conversation_summary(conversation_id: str) -> dict[str, Any]:
    conv = get_conversation(conversation_id)
    if not conv.get("ok"):
        return conv

    messages = conv.get("messages", [])
    if not isinstance(messages, list):
        messages = []

    summary = summarize_messages(messages[-80:])

    conv["summary"] = summary
    conv["summary_updated_at"] = now_iso()

    save_json(CONV_DIR / f"{conversation_id}.json", conv)

    report = {
        "ok": True,
        "tool": "Conversation Summary Engine",
        "timestamp": now_iso(),
        "conversation_id": conversation_id,
        "title": conv.get("title"),
        "messages": len(messages),
        "summary": summary,
    }

    report_path = REPORTS / f"conversation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, report)
    report["report_path"] = str(report_path)

    return report


def summary_context(conversation_id: str | None) -> str:
    if not conversation_id:
        return ""

    conv = get_conversation(conversation_id)
    if not conv.get("ok"):
        return ""

    return clean(conv.get("summary", ""))


if __name__ == "__main__":
    import sys
    cid = sys.argv[1] if len(sys.argv) > 1 else ""
    print(json.dumps(update_conversation_summary(cid), indent=2, ensure_ascii=False))
