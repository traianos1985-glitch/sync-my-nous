from __future__ import annotations

import json
import re
from typing import Any

from executor.conversation_manager import get_conversation, rename_conversation, load_json, INDEX


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def strip_prefixes(text: str) -> str:
    t = clean(text)

    prefixes = [
        "Σημείωσε ότι ",
        "Σημειωσε οτι ",
        "Μιλάμε για ",
        "Μιλαμε για ",
        "Θέλω να ",
        "Θελω να ",
        "Επίσης θέλω να ",
        "Επισης θελω να ",
        "Αυτή είναι ",
        "Αυτη ειναι ",
    ]

    for p in prefixes:
        if t.lower().startswith(p.lower()):
            t = t[len(p):].strip()
            break

    return t


def is_search_or_memory_prompt(text: str) -> bool:
    low = clean(text).lower()
    return any(x in low for x in [
        "βρες τη συνομιλία",
        "βρες την συνομιλία",
        "ψάξε στις συνομιλίες",
        "ψαξε στις συνομιλιες",
        "θυμάσαι τι",
        "θυμασαι τι",
        "σε ποια συνομιλία",
        "σε ποια συνομιλια",
    ])


def nice_title_from_user_messages(messages: list[dict[str, Any]]) -> str:
    candidates = []

    for m in messages:
        if not isinstance(m, dict) or m.get("role") != "user":
            continue

        content = strip_prefixes(m.get("content", ""))
        if not content:
            continue

        if is_search_or_memory_prompt(content):
            continue

        content = content.strip(" .;:!?")
        if len(content) < 8:
            continue

        candidates.append(content)

    if not candidates:
        return "Νέα συνομιλία"

    title = candidates[0]

    title = title.replace("semantic search", "Semantic Search")
    title = title.replace("deep research", "Deep Research")
    title = title.replace("long memory", "Long Memory")
    title = title.replace("AI agents", "AI Agents")
    title = title.replace("ai agents", "AI Agents")

    if len(title) > 58:
        title = title[:58].rstrip() + "..."

    return clean(title)


def generate_conversation_title(conversation_id: str) -> dict[str, Any]:
    conv = get_conversation(conversation_id)
    if not conv.get("ok"):
        return conv

    msgs = conv.get("messages", [])
    if not isinstance(msgs, list):
        msgs = []

    title = nice_title_from_user_messages(msgs)
    return rename_conversation(conversation_id, title)


def auto_title_recent_conversations(limit: int = 80) -> dict[str, Any]:
    index = load_json(INDEX, [])
    if not isinstance(index, list):
        index = []

    updated = []

    ugly_markers = [
        "Σημε", "Στημα", "Συνομιλ", "Αποφασ", "Ληψη", "Δοκιμαστικ",
        "συνομιλ", "αποθ", "κευσης", "μιλο", "σαμε"
    ]

    for item in index[:limit]:
        if not isinstance(item, dict):
            continue

        cid = item.get("id")
        title = str(item.get("title", ""))

        if not cid:
            continue

        ugly = any(x in title for x in ugly_markers)
        too_long = len(title) > 65
        generic = title.startswith((
            "Μιλάμε", "Μιλαμε", "Σημείωσε", "Σημειωσε",
            "Αυτή είναι", "Αυτη ειναι", "Γεια",
            "βρες τη συνομιλία", "θυμάσαι τι"
        ))

        if ugly or too_long or generic:
            res = generate_conversation_title(str(cid))
            if res.get("ok"):
                updated.append(res)

    return {
        "ok": True,
        "updated": updated,
        "total": len(updated),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(json.dumps(generate_conversation_title(sys.argv[1]), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(auto_title_recent_conversations(), indent=2, ensure_ascii=False))
