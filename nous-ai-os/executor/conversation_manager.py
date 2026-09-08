from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA = Path("data")
CONV_DIR = DATA / "conversations"
INDEX = DATA / "conversation_index.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def safe_title(text: str, fallback: str = "Νέα συνομιλία") -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    t = t[:70].strip()
    return t or fallback


def new_conversation(title: str = "") -> dict[str, Any]:
    CONV_DIR.mkdir(parents=True, exist_ok=True)

    cid = str(int(time.time() * 1000000))
    title = safe_title(title, "Νέα συνομιλία")

    conv = {
        "ok": True,
        "id": cid,
        "title": title,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "messages": [],
        "summary": "",
    }

    save_json(CONV_DIR / f"{cid}.json", conv)

    index = load_json(INDEX, [])
    if not isinstance(index, list):
        index = []

    index.insert(0, {
        "id": cid,
        "title": title,
        "created_at": conv["created_at"],
        "updated_at": conv["updated_at"],
        "messages": 0,
    })

    save_json(INDEX, index[:200])
    return conv


def get_conversation(conversation_id: str) -> dict[str, Any]:
    path = CONV_DIR / f"{conversation_id}.json"
    conv = load_json(path, None)
    if not isinstance(conv, dict):
        return {"ok": False, "error": "conversation_not_found", "id": conversation_id}
    conv["ok"] = True
    return conv


def list_conversations(limit: int = 30) -> dict[str, Any]:
    index = load_json(INDEX, [])
    if not isinstance(index, list):
        index = []
    return {
        "ok": True,
        "total": len(index),
        "conversations": index[:limit],
    }


def update_index(conv: dict[str, Any]) -> None:
    index = load_json(INDEX, [])
    if not isinstance(index, list):
        index = []

    item = {
        "id": conv["id"],
        "title": conv.get("title", "Συνομιλία"),
        "created_at": conv.get("created_at"),
        "updated_at": conv.get("updated_at"),
        "messages": len(conv.get("messages", [])),
    }

    index = [x for x in index if not (isinstance(x, dict) and x.get("id") == conv["id"])]
    index.insert(0, item)
    save_json(INDEX, index[:200])


def append_turn(
    user_message: str,
    assistant_answer: str,
    mode: str = "chat",
    conversation_id: str | None = None,
    title: str = "",
) -> dict[str, Any]:
    if conversation_id:
        conv = get_conversation(conversation_id)
        if not conv.get("ok"):
            conv = new_conversation(title or user_message)
    else:
        conv = new_conversation(title or user_message)

    conv.setdefault("messages", [])
    conv["messages"].append({
        "time": now_iso(),
        "role": "user",
        "content": user_message,
    })
    conv["messages"].append({
        "time": now_iso(),
        "role": "assistant",
        "mode": mode,
        "content": assistant_answer,
    })

    conv["updated_at"] = now_iso()

    if not conv.get("title") or conv.get("title") == "Νέα συνομιλία":
        conv["title"] = safe_title(user_message)

    save_json(CONV_DIR / f"{conv['id']}.json", conv)
    update_index(conv)

    return {
        "ok": True,
        "conversation_id": conv["id"],
        "title": conv.get("title"),
        "messages": len(conv.get("messages", [])),
    }


def conversation_context(conversation_id: str | None, limit: int = 8) -> str:
    if not conversation_id:
        return ""

    conv = get_conversation(conversation_id)
    if not conv.get("ok"):
        return ""

    messages = conv.get("messages", [])
    if not isinstance(messages, list):
        return ""

    recent = messages[-limit:]
    lines = []

    for m in recent:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = str(m.get("content", "")).strip()
        if not content:
            continue
        if len(content) > 600:
            content = content[:600].rstrip() + "..."
        label = "Χρήστης" if role == "user" else "ΝΟΥΣ"
        lines.append(f"{label}: {content}")

    return "\n".join(lines)


def rename_conversation(conversation_id: str, title: str) -> dict[str, Any]:
    conv = get_conversation(conversation_id)
    if not conv.get("ok"):
        return conv

    conv["title"] = safe_title(title)
    conv["updated_at"] = now_iso()

    save_json(CONV_DIR / f"{conv['id']}.json", conv)
    update_index(conv)

    return {"ok": True, "conversation_id": conv["id"], "title": conv["title"]}


def delete_conversation(conversation_id: str) -> dict[str, Any]:
    path = CONV_DIR / f"{conversation_id}.json"
    if path.exists():
        path.unlink()

    index = load_json(INDEX, [])
    if not isinstance(index, list):
        index = []

    index = [x for x in index if not (isinstance(x, dict) and x.get("id") == conversation_id)]
    save_json(INDEX, index)

    return {"ok": True, "deleted": conversation_id}


if __name__ == "__main__":
    print(json.dumps(list_conversations(), indent=2, ensure_ascii=False))
