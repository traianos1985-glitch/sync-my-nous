from __future__ import annotations

import json
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from executor import shared_state_store

DATA = Path("data")
CONV_DIR = DATA / "conversations"
INDEX = DATA / "conversation_index.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if shared_state_store.cloud_enabled():
        return shared_state_store.read_state(path, default)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Invalid JSON in {path}") from exc


def save_json(path: Path, data: Any) -> None:
    if shared_state_store.cloud_enabled():
        shared_state_store.write_state(path, data)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(payload)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _valid_conversation_id(conversation_id: str) -> bool:
    # IDs are generated from microsecond timestamps; reject path separators and traversal.
    return bool(re.fullmatch(r"[0-9]{1,30}", str(conversation_id or "")))


def normalize_limit(value: Any, default: int = 8, maximum: int = 50) -> int:
    """Normalize API-supplied list limits without raising or permitting unbounded work."""
    try:
        if isinstance(value, bool):
            raise ValueError("boolean is not a limit")
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        parsed = default
    return max(1, min(parsed, maximum))


def _load_index() -> list[dict[str, Any]]:
    """Read the conversation index without silently replacing unexpected data."""
    index = load_json(INDEX, [])
    if not isinstance(index, list):
        raise ValueError(f"Invalid conversation index structure in {INDEX}")
    return [item for item in index if isinstance(item, dict)]


def _upsert_index_item(item: dict[str, Any]) -> None:
    if shared_state_store.cloud_enabled():
        with shared_state_store.edit_state(INDEX, []) as index:
            if not isinstance(index, list):
                raise ValueError(f"Invalid conversation index structure in {INDEX}")
            index[:] = [x for x in index if not (isinstance(x, dict) and x.get("id") == item["id"])]
            index.insert(0, item)
            del index[200:]
        return
    index = _load_index()
    index = [x for x in index if not (isinstance(x, dict) and x.get("id") == item["id"])]
    index.insert(0, item)
    save_json(INDEX, index[:200])


def _remove_index_item(conversation_id: str) -> None:
    if shared_state_store.cloud_enabled():
        with shared_state_store.edit_state(INDEX, []) as index:
            if not isinstance(index, list):
                raise ValueError(f"Invalid conversation index structure in {INDEX}")
            index[:] = [x for x in index if not (isinstance(x, dict) and x.get("id") == conversation_id)]
        return
    index = [x for x in _load_index() if x.get("id") != conversation_id]
    save_json(INDEX, index)


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

    # Validate the index before creating the conversation file, so corrupt
    # metadata cannot leave behind a newly-created orphan conversation.
    _load_index()

    save_json(CONV_DIR / f"{cid}.json", conv)

    _upsert_index_item({
        "id": cid,
        "title": title,
        "created_at": conv["created_at"],
        "updated_at": conv["updated_at"],
        "messages": 0,
    })
    return conv


def get_conversation(conversation_id: str) -> dict[str, Any]:
    if not _valid_conversation_id(conversation_id):
        return {"ok": False, "error": "conversation_not_found", "id": conversation_id}
    path = CONV_DIR / f"{conversation_id}.json"
    conv = load_json(path, None)
    if not isinstance(conv, dict) or conv.get("deleted") is True:
        return {"ok": False, "error": "conversation_not_found", "id": conversation_id}
    conv["ok"] = True
    return conv


def list_conversations(limit: int = 30) -> dict[str, Any]:
    index = _load_index()
    bounded_limit = normalize_limit(limit, default=30, maximum=200)
    return {
        "ok": True,
        "total": len(index),
        "conversations": index[:bounded_limit],
    }


def update_index(conv: dict[str, Any]) -> None:
    _load_index()

    item = {
        "id": conv["id"],
        "title": conv.get("title", "Συνομιλία"),
        "created_at": conv.get("created_at"),
        "updated_at": conv.get("updated_at"),
        "messages": len(conv.get("messages", [])),
    }

    _upsert_index_item(item)


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

    # Refuse to mutate a conversation if the shared index is already corrupt.
    _load_index()
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

    _load_index()
    conv["title"] = safe_title(title)
    conv["updated_at"] = now_iso()

    save_json(CONV_DIR / f"{conv['id']}.json", conv)
    update_index(conv)

    return {"ok": True, "conversation_id": conv["id"], "title": conv["title"]}


def delete_conversation(conversation_id: str) -> dict[str, Any]:
    if not _valid_conversation_id(conversation_id):
        return {"ok": False, "error": "conversation_not_found", "id": conversation_id}
    _load_index()
    path = CONV_DIR / f"{conversation_id}.json"
    if shared_state_store.cloud_enabled():
        save_json(path, {"id": conversation_id, "deleted": True, "deleted_at": now_iso()})
    elif path.exists():
        path.unlink()

    _remove_index_item(conversation_id)

    return {"ok": True, "deleted": conversation_id}


if __name__ == "__main__":
    print(json.dumps(list_conversations(), indent=2, ensure_ascii=False))
