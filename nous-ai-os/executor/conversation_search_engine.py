from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from executor.conversation_manager import CONV_DIR, INDEX, get_conversation, load_json, save_json

REPORTS = Path("data/reports")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-zΑ-Ωα-ω0-9_]{3,}", str(text or "").lower())


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def conversation_text(conv: dict[str, Any]) -> str:
    parts = [
        conv.get("title", ""),
        conv.get("summary", ""),
    ]

    msgs = conv.get("messages", [])
    if isinstance(msgs, list):
        for m in msgs:
            if isinstance(m, dict):
                parts.append(str(m.get("content", "")))

    return "\n".join(parts)




def is_search_noise_conversation(conv: dict[str, Any]) -> bool:
    msgs = conv.get("messages", [])
    if not isinstance(msgs, list) or not msgs:
        return False

    user_msgs = [
        str(m.get("content", "")).lower()
        for m in msgs
        if isinstance(m, dict) and m.get("role") == "user"
    ]

    if not user_msgs:
        return False

    noise_hits = 0
    for u in user_msgs:
        if any(x in u for x in [
            "βρες τη συνομιλία",
            "βρες την συνομιλία",
            "ψάξε στις συνομιλίες",
            "ψαξε στις συνομιλιες",
            "θυμάσαι τι αποφασίσαμε",
            "θυμασαι τι αποφασισαμε",
        ]):
            noise_hits += 1

    return noise_hits >= max(1, len(user_msgs))


def score_conversation(query: str, conv: dict[str, Any]) -> dict[str, Any]:
    q_tokens = set(tokenize(query))
    text = conversation_text(conv)
    t_tokens = set(tokenize(text))

    score = len(q_tokens & t_tokens) * 5

    low = text.lower()
    for q in q_tokens:
        if q in low:
            score += 2

    title = str(conv.get("title", "")).lower()
    for q in q_tokens:
        if q in title:
            score += 5

    summary = str(conv.get("summary", "")).lower()
    for q in q_tokens:
        if q in summary:
            score += 4

    excerpt = ""
    msgs = conv.get("messages", [])
    if isinstance(msgs, list):
        for m in msgs:
            if not isinstance(m, dict):
                continue
            content = clean(m.get("content", ""))
            clow = content.lower()
            if any(q in clow for q in q_tokens):
                excerpt = content[:700]
                break

    if not excerpt:
        excerpt = clean(conv.get("summary", ""))[:700]

    return {
        "conversation_id": conv.get("id"),
        "title": conv.get("title"),
        "score": score,
        "updated_at": conv.get("updated_at"),
        "messages": len(conv.get("messages", [])) if isinstance(conv.get("messages", []), list) else 0,
        "excerpt": excerpt,
    }


def search_conversations(query: str, limit: int = 8) -> dict[str, Any]:
    query = clean(query)
    if not query:
        return {"ok": False, "error": "empty_query", "query": query}

    index = load_json(INDEX, [])
    if not isinstance(index, list):
        index = []

    hits = []
    for item in index:
        if not isinstance(item, dict):
            continue

        cid = item.get("id")
        if not cid:
            continue

        conv = get_conversation(str(cid))
        if not conv.get("ok"):
            continue

        # Skip pure search/memory-recall conversations so results do not pollute themselves.
        if is_search_noise_conversation(conv):
            continue

        scored = score_conversation(query, conv)
        if scored["score"] > 0:
            hits.append(scored)

    hits.sort(key=lambda x: (x.get("score", 0), x.get("updated_at", "")), reverse=True)

    result = {
        "ok": True,
        "tool": "Conversation Search Engine",
        "timestamp": now_iso(),
        "query": query,
        "total": len(hits),
        "hits": hits[:limit],
    }

    report = REPORTS / f"conversation_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report, result)
    result["report_path"] = str(report)

    return result


def answer_from_conversations(query: str) -> dict[str, Any]:
    res = search_conversations(query)

    if not res.get("ok"):
        return {
            "ok": False,
            "answer": "Δεν μπόρεσα να ψάξω στις παλιές συνομιλίες.",
            "raw": res,
        }

    hits = res.get("hits", [])

    if not hits:
        return {
            "ok": True,
            "answer": "Δεν βρήκα σχετική παλιά συνομιλία.",
            "hits": [],
            "raw": res,
        }

    lines = ["Βρήκα σχετικές παλιές συνομιλίες:"]
    for i, h in enumerate(hits, 1):
        lines.append("")
        lines.append(f"{i}. {h.get('title')}")
        lines.append(f"   ID: {h.get('conversation_id')}")
        lines.append(f"   Score: {h.get('score')}")
        if h.get("excerpt"):
            lines.append(f"   Απόσπασμα: {h.get('excerpt')}")

    return {
        "ok": True,
        "answer": "\n".join(lines),
        "hits": hits,
        "raw": res,
    }


def cross_conversation_context(query: str, limit: int = 5) -> str:
    res = search_conversations(query, limit=limit)
    hits = res.get("hits", []) if res.get("ok") else []

    if not hits:
        return ""

    lines = ["Σχετική μνήμη από παλιές συνομιλίες:"]
    for h in hits:
        lines.append("")
        lines.append(f"• {h.get('title')} / ID: {h.get('conversation_id')}")
        if h.get("excerpt"):
            lines.append(f"  {h.get('excerpt')[:500]}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    print(json.dumps(answer_from_conversations(" ".join(sys.argv[1:])), indent=2, ensure_ascii=False))
