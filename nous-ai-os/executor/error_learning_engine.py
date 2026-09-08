from __future__ import annotations

import json, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA = Path("data")
ERROR_MEMORY = DATA / "error_learning_memory.json"
SOLUTION_MEMORY = DATA / "coding_solution_memory.json"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-zΑ-Ωα-ω0-9_]{3,}", clean(text).lower())


def make_id(*parts: str) -> str:
    raw = "|".join(clean(x).lower() for x in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def score_text(query: str, text: str) -> int:
    q = set(tokenize(query))
    t = set(tokenize(text))
    if not q or not t:
        return 0
    return len(q & t) * 10


def remember_error(
    error_type: str,
    message: str,
    file: str = "",
    command: str = "",
    fix: str = "",
    status: str = "open",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    errors = load_json(ERROR_MEMORY, [])
    if not isinstance(errors, list):
        errors = []

    eid = make_id(error_type, message, file, fix)

    item = {
        "id": eid,
        "error_type": clean(error_type),
        "message": clean(message),
        "file": clean(file),
        "command": clean(command),
        "fix": clean(fix),
        "status": clean(status) or "open",
        "tags": tags or tokenize(" ".join([error_type, message, file, fix]))[:12],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "uses": 0,
    }

    for i, old in enumerate(errors):
        if isinstance(old, dict) and old.get("id") == eid:
            item["created_at"] = old.get("created_at", item["created_at"])
            item["uses"] = int(old.get("uses", 0))
            errors[i] = item
            save_json(ERROR_MEMORY, errors[:2000])
            return {"ok": True, "stored": False, "id": eid, "item": item}

    errors.insert(0, item)
    save_json(ERROR_MEMORY, errors[:2000])
    return {"ok": True, "stored": True, "id": eid, "item": item}


def search_errors(query: str, limit: int = 8) -> dict[str, Any]:
    errors = load_json(ERROR_MEMORY, [])
    if not isinstance(errors, list):
        errors = []

    hits = []
    for item in errors:
        if not isinstance(item, dict):
            continue

        text = "\n".join([
            str(item.get("error_type", "")),
            str(item.get("message", "")),
            str(item.get("file", "")),
            str(item.get("command", "")),
            str(item.get("fix", "")),
            " ".join(item.get("tags", [])),
        ])

        score = score_text(query, text)
        if score > 0:
            h = dict(item)
            h["score"] = score
            hits.append(h)

    hits.sort(key=lambda x: (x.get("score", 0), x.get("updated_at", "")), reverse=True)
    return {"ok": True, "query": clean(query), "total": len(hits), "hits": hits[:limit], "timestamp": now_iso()}


def remember_solution(
    problem: str,
    solution: str,
    files: list[str] | None = None,
    status: str = "successful",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    solutions = load_json(SOLUTION_MEMORY, [])
    if not isinstance(solutions, list):
        solutions = []

    sid = make_id(problem, solution, " ".join(files or []))

    item = {
        "id": sid,
        "problem": clean(problem),
        "solution": clean(solution),
        "files": files or [],
        "status": clean(status) or "successful",
        "tags": tags or tokenize(problem + " " + solution + " " + " ".join(files or []))[:12],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "uses": 0,
    }

    for i, old in enumerate(solutions):
        if isinstance(old, dict) and old.get("id") == sid:
            item["created_at"] = old.get("created_at", item["created_at"])
            item["uses"] = int(old.get("uses", 0))
            solutions[i] = item
            save_json(SOLUTION_MEMORY, solutions[:2000])
            return {"ok": True, "stored": False, "id": sid, "item": item}

    solutions.insert(0, item)
    save_json(SOLUTION_MEMORY, solutions[:2000])
    return {"ok": True, "stored": True, "id": sid, "item": item}


def search_solutions(query: str, limit: int = 8) -> dict[str, Any]:
    solutions = load_json(SOLUTION_MEMORY, [])
    if not isinstance(solutions, list):
        solutions = []

    hits = []
    for item in solutions:
        if not isinstance(item, dict):
            continue

        text = "\n".join([
            str(item.get("problem", "")),
            str(item.get("solution", "")),
            " ".join(item.get("files", [])),
            " ".join(item.get("tags", [])),
        ])

        score = score_text(query, text)
        if score > 0:
            h = dict(item)
            h["score"] = score
            hits.append(h)

    hits.sort(key=lambda x: (x.get("score", 0), x.get("updated_at", "")), reverse=True)
    return {"ok": True, "query": clean(query), "total": len(hits), "hits": hits[:limit], "timestamp": now_iso()}


def engineering_memory_context(query: str) -> str:
    errors = search_errors(query, limit=5).get("hits", [])
    solutions = search_solutions(query, limit=5).get("hits", [])

    lines = []

    if errors:
        lines.append("Παλιά λάθη που πρέπει να αποφύγεις:")
        for e in errors:
            fix = e.get("fix") or "Δεν έχει καταγραφεί fix."
            lines.append(f"• {e.get('error_type')}: {e.get('message')} | Fix: {fix}")

    if solutions:
        if lines:
            lines.append("")
        lines.append("Παλιά επιτυχημένα patterns που μπορείς να ξαναχρησιμοποιήσεις:")
        for s in solutions:
            files = ", ".join(s.get("files", []))
            lines.append(f"• {s.get('problem')} → {s.get('solution')} | Files: {files}")

    return "\n".join(lines)


def status() -> dict[str, Any]:
    errors = load_json(ERROR_MEMORY, [])
    solutions = load_json(SOLUTION_MEMORY, [])
    return {
        "ok": True,
        "tool": "Error Learning Engine",
        "errors": len(errors) if isinstance(errors, list) else 0,
        "solutions": len(solutions) if isinstance(solutions, list) else 0,
        "error_memory": str(ERROR_MEMORY),
        "solution_memory": str(SOLUTION_MEMORY),
        "timestamp": now_iso(),
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2, ensure_ascii=False))
