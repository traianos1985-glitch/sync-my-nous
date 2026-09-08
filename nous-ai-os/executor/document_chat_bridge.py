from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from executor.document_intelligence_engine import answer_from_documents, status
from executor.document_answer_engine import answer_question


def now_iso():
    return datetime.now(timezone.utc).isoformat()


DOC_TRIGGERS = [
    "έγγραφο", "εγχειρίδιο", "manual", "pdf", "docx",
    "αρχείο", "αρχεία", "μαθημένα", "τι λέει",
    "σύμφωνα με", "θυμάσαι από το αρχείο",
    "κρύπτες", "κρυπτες", "πέτρες", "πετρες",
    "απόκρυψη", "αποκρυψη", "αποκρύψεις", "αποκρυψεις",
    "αποκρυψεων", "αποκρύψεων"
]


def should_use_documents(message: str) -> bool:
    m = (message or "").lower()
    return any(t in m for t in DOC_TRIGGERS)


def document_chat_answer(message: str) -> dict[str, Any]:
    if not should_use_documents(message):
        return {
            "ok": True,
            "used_documents": False,
            "answer": None,
            "sources": [],
        }

    result = answer_from_documents(message)

    return {
        "ok": True,
        "used_documents": True,
        "timestamp": now_iso(),
        "question": message,
        "document_status": status(),
        "answer": result.get("answer"),
        "sources": result.get("sources", []),
        "raw": result,
    }


def format_document_answer(message: str) -> str:
    result = document_chat_answer(message)

    if not result.get("used_documents"):
        return ""

    sources = result.get("sources", [])
    if not sources:
        return "Δεν βρήκα σχετική πληροφορία στα μαθημένα έγγραφα."

    try:
        v2 = answer_question(message)
        answer = v2.get("answer")
        if isinstance(answer, str) and answer.strip():
            return answer
    except Exception:
        pass

    return build_human_document_answer(message, sources)


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "status"
    print(json.dumps(document_chat_answer(q), indent=2, ensure_ascii=False))


def build_human_document_answer(question: str, sources: list) -> str:
    if not sources:
        return "Δεν βρήκα σχετική πληροφορία στα μαθημένα έγγραφα."

    excerpts = []

    for src in sources[:3]:
        text = str(src.get("excerpt", "")).strip()
        if text:
            excerpts.append(text)

    merged = "\n".join(excerpts)

    lines = []

    for line in merged.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.lower().startswith("εγχειρίδιο"):
            continue

        if line not in lines:
            lines.append(line)

    if not lines:
        return "Βρήκα σχετικές πληροφορίες αλλά δεν μπόρεσα να δημιουργήσω περίληψη."

    bullets = []

    for line in lines[:8]:
        bullets.append("• " + line)

    return (
        "Σύμφωνα με τα μαθημένα έγγραφα:\n\n"
        + "\n".join(bullets)
    )

