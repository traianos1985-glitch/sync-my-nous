from __future__ import annotations

import json, os, re, hashlib, tempfile, threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from executor import portable_fcntl as fcntl
from executor import shared_state_store

DATA = Path("data")
KNOWLEDGE_FILE = DATA / "knowledge_memory.json"
CODE_LESSONS_FILE = DATA / "code_lessons_memory.json"

# N-07 bounds: the store must never grow without limit or hold oversized blobs.
MAX_KNOWLEDGE_ITEMS = 2000
MAX_CODE_LESSONS = 1000
MAX_QUESTION_CHARS = 1000
MAX_ANSWER_CHARS = 8000
MAX_SOURCES = 10
MAX_SOURCE_CHARS = 500
MAX_FILE_BYTES = 5 * 1024 * 1024
# Unverified web-derived answers age out; documents/manual knowledge do not by default.
DEFAULT_TTL_DAYS = {"web": 30}

_thread_lock = threading.RLock()
_lock_depth = threading.local()

def now_iso(): return datetime.now(timezone.utc).isoformat()

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()

def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-zΑ-Ωα-ω0-9_]{3,}", clean(text).lower())

def make_id(*parts: str) -> str:
    raw = "|".join(clean(x).lower() for x in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

@contextmanager
def _store_lock(path: Path):
    """Process-wide + cross-process exclusive lock; re-entrant within one thread."""
    key = str(Path(path).resolve())
    depths = getattr(_lock_depth, "depths", None)
    if depths is None:
        depths = _lock_depth.depths = {}
    with _thread_lock:
        if depths.get(key):
            depths[key] += 1
            try:
                yield
            finally:
                depths[key] -= 1
            return
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(str(path) + ".lock", "a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            depths[key] = 1
            try:
                yield
            finally:
                depths[key] = 0
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

def load_json(path: Path, default: Any) -> Any:
    if shared_state_store.cloud_enabled():
        return shared_state_store.read_state(path, default)
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default

def _encode_bounded(data: Any) -> str:
    encoded = json.dumps(data, indent=2, ensure_ascii=False)
    if isinstance(data, list):
        items = list(data)
        # Drop the oldest entries (lists are newest-first) until under the byte budget.
        while items and len(encoded.encode("utf-8")) > MAX_FILE_BYTES:
            items = items[: max(0, int(len(items) * 0.9))]
            encoded = json.dumps(items, indent=2, ensure_ascii=False)
    return encoded

def save_json(path: Path, data: Any) -> None:
    """Atomic local write or transactional cloud document update."""
    path = Path(path)
    if shared_state_store.cloud_enabled():
        shared_state_store.write_state(path, data)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = _encode_bounded(data)
    with _store_lock(path):
        fd, temp_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

def _normalize_sources(sources) -> list:
    if not isinstance(sources, (list, tuple)):
        sources = [sources] if sources else []
    out = []
    for source in list(sources)[:MAX_SOURCES]:
        if isinstance(source, dict):
            item = {k: clean(source.get(k))[:MAX_SOURCE_CHARS] for k in ("url", "title") if source.get(k)}
            if item:
                out.append(item)
        elif source not in (None, ""):
            out.append(clean(source)[:MAX_SOURCE_CHARS])
    return out

def _is_expired(item: dict, now: datetime | None = None) -> bool:
    expires = item.get("expires_at")
    if not expires:
        return False
    try:
        return datetime.fromisoformat(str(expires)) <= (now or datetime.now(timezone.utc))
    except ValueError:
        return False

def score_text(query: str, text: str) -> int:
    q, t = set(tokenize(query)), set(tokenize(text))
    if not q or not t: return 0
    score = len(q & t) * 8
    low = clean(text).lower()
    for token in q:
        if token in low: score += 2
    return score

def remember_knowledge(question: str, answer: str, sources=None, kind="general", confidence="medium", tags=None,
                       origin: str | None = None, ttl_days: int | None = None):
    question, answer = clean(question), clean(answer)
    if not question or not answer:
        return {"ok": False, "error": "empty_question_or_answer"}
    if len(question) > MAX_QUESTION_CHARS:
        return {"ok": False, "error": "question_too_long", "max_chars": MAX_QUESTION_CHARS}
    truncated = len(answer) > MAX_ANSWER_CHARS
    answer = answer[:MAX_ANSWER_CHARS]
    kind = clean(kind)[:40] or "general"
    sources = _normalize_sources(sources)
    if ttl_days is None:
        ttl_days = DEFAULT_TTL_DAYS.get(kind)
    stored_at = now_iso()

    kid = make_id(kind, question, answer[:180])
    item = {
        "id": kid,
        "kind": kind,
        "question": question,
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
        "tags": [clean(t)[:60] for t in (tags or tokenize(question)[:12])][:20],
        "created_at": stored_at,
        "updated_at": stored_at,
        "uses": 0,
        # Provenance: where this came from and that NOUS has not independently verified it.
        "provenance": {
            "origin": clean(origin or kind)[:60],
            "stored_at": stored_at,
            "source_count": len(sources),
            "verified": False,
            "answer_truncated": truncated,
        },
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=int(ttl_days))).isoformat() if ttl_days else None,
    }

    with _store_lock(KNOWLEDGE_FILE):
        memory = load_json(KNOWLEDGE_FILE, [])
        if not isinstance(memory, list): memory = []
        for i, old in enumerate(memory):
            if isinstance(old, dict) and old.get("id") == kid:
                item["created_at"] = old.get("created_at", item["created_at"])
                item["uses"] = int(old.get("uses", 0) or 0)
                memory[i] = item
                save_json(KNOWLEDGE_FILE, memory[:MAX_KNOWLEDGE_ITEMS])
                return {"ok": True, "stored": False, "id": kid, "item": item}
        memory.insert(0, item)
        save_json(KNOWLEDGE_FILE, memory[:MAX_KNOWLEDGE_ITEMS])
    return {"ok": True, "stored": True, "id": kid, "item": item}

def search_knowledge(query: str, limit=5, min_score=10):
    memory = load_json(KNOWLEDGE_FILE, [])
    if not isinstance(memory, list): memory = []

    hits = []
    for item in memory:
        if not isinstance(item, dict) or _is_expired(item): continue
        text = "\n".join([
            str(item.get("question", "")),
            str(item.get("answer", "")),
            " ".join(str(x) for x in item.get("tags", [])),
        ])
        score = score_text(query, text)
        if score >= min_score:
            h = dict(item)
            h["score"] = score
            hits.append(h)

    hits.sort(key=lambda x: (x.get("score", 0), x.get("updated_at", "")), reverse=True)
    return {"ok": True, "query": clean(query), "total": len(hits), "hits": hits[:limit], "timestamp": now_iso()}

def answer_from_knowledge_memory(query: str):
    res = search_knowledge(query, limit=3, min_score=14)
    hits = res.get("hits", [])
    if not hits:
        return {"ok": True, "found": False, "answer": "", "hits": []}

    best = hits[0]
    answer = best.get("answer", "")

    with _store_lock(KNOWLEDGE_FILE):
        memory = load_json(KNOWLEDGE_FILE, [])
        if isinstance(memory, list):
            for item in memory:
                if isinstance(item, dict) and item.get("id") == best.get("id"):
                    item["uses"] = int(item.get("uses", 0) or 0) + 1
                    item["last_used_at"] = now_iso()
                    break
            save_json(KNOWLEDGE_FILE, memory[:MAX_KNOWLEDGE_ITEMS])

    return {
        "ok": True,
        "found": True,
        "mode": "knowledge_memory",
        "answer": "Το βρήκα στη μόνιμη μνήμη γνώσης:\n\n" + answer,
        "hits": hits,
        "provenance": best.get("provenance"),
    }

def should_store_answer(mode: str, answer: str, sources=None) -> bool:
    if mode not in {"internet_search", "deep_research", "url_reader", "document_recall"}:
        return False
    answer = clean(answer)
    if len(answer) < 80: return False
    low = answer.lower()
    if any(x in low for x in ["δεν μπόρεσα", "δεν βρήκα", "δεν είμαι βέβαιος", "άγνωστο σφάλμα"]):
        return False
    if mode in {"internet_search", "deep_research", "url_reader"} and not sources:
        return False
    return True

def learn_from_chat_result(question: str, answer: str, mode: str, sources=None):
    if not should_store_answer(mode, answer, sources):
        return {"ok": True, "stored": False, "reason": "not_suitable"}
    kind = "web" if mode in {"internet_search", "deep_research", "url_reader"} else "document"
    return remember_knowledge(question, answer, sources or [], kind, "medium", tokenize(question)[:12],
                              origin=f"chat:{mode}")

def seed_code_lessons():
    with _store_lock(CODE_LESSONS_FILE):
        lessons = load_json(CODE_LESSONS_FILE, [])
        if not isinstance(lessons, list): lessons = []

        base = [
            ("mobile termux patches", "Ο χρήστης δουλεύει κυρίως από Android/Termux. Δίνε μεγάλες copy-paste εντολές και όχι μικρο-αλλαγές γραμμών.", "high", ["termux","android","copy-paste"]),
            ("python code changes", "Μετά από κάθε αλλαγή Python πρέπει να τρέχει py_compile στα επηρεαζόμενα αρχεία πριν από commit.", "high", ["python","py_compile"]),
            ("git workflow", "Πριν από push να γίνεται git status και commit μόνο ουσιαστικών αρχείων, όχι runtime reports/cache εκτός αν ζητηθεί.", "high", ["git","commit"]),
            ("NOUS architecture", "Μην ξανασχεδιάζεις τον ΝΟΥΣ από την αρχή. Κάνε σταθερές αναβαθμίσεις πάνω στην υπάρχουσα αρχιτεκτονική.", "critical", ["nous","architecture"]),
            ("chat missions", "Το chat δεν πρέπει να δημιουργεί mission μόνο του. Mission μόνο με ρητή εντολή /plan, /run ή explicit command.", "critical", ["chat","mission"]),
        ]

        ids = {x.get("id") for x in lessons if isinstance(x, dict)}
        for trigger, lesson, severity, tags in base:
            lid = make_id(trigger, lesson)
            if lid not in ids:
                lessons.insert(0, {
                    "id": lid,
                    "trigger": trigger,
                    "lesson": lesson,
                    "severity": severity,
                    "tags": tags,
                    "created_at": now_iso(),
                    "updated_at": now_iso(),
                    "uses": 0,
                })

        save_json(CODE_LESSONS_FILE, lessons[:MAX_CODE_LESSONS])

def remember_code_lesson(trigger: str, lesson: str, files=None, severity="medium", tags=None):
    seed_code_lessons()
    trigger, lesson = clean(trigger), clean(lesson)
    if not trigger or not lesson:
        return {"ok": False, "error": "empty_trigger_or_lesson"}

    with _store_lock(CODE_LESSONS_FILE):
        return _remember_code_lesson_locked(trigger, lesson, files, severity, tags)


def _remember_code_lesson_locked(trigger, lesson, files, severity, tags):
    lessons = load_json(CODE_LESSONS_FILE, [])
    if not isinstance(lessons, list): lessons = []

    lid = make_id(trigger, lesson)
    item = {
        "id": lid,
        "trigger": trigger,
        "lesson": lesson,
        "files": files or [],
        "severity": severity,
        "tags": tags or tokenize(trigger + " " + lesson)[:10],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "uses": 0,
    }

    for i, old in enumerate(lessons):
        if isinstance(old, dict) and old.get("id") == lid:
            item["created_at"] = old.get("created_at", item["created_at"])
            item["uses"] = int(old.get("uses", 0))
            lessons[i] = item
            save_json(CODE_LESSONS_FILE, lessons[:1000])
            return {"ok": True, "stored": False, "id": lid, "item": item}

    lessons.insert(0, item)
    save_json(CODE_LESSONS_FILE, lessons[:1000])
    return {"ok": True, "stored": True, "id": lid, "item": item}

def search_code_lessons(query: str, limit=8, min_score=0):
    seed_code_lessons()
    lessons = load_json(CODE_LESSONS_FILE, [])
    if not isinstance(lessons, list): lessons = []

    hits = []
    for item in lessons:
        if not isinstance(item, dict): continue
        text = "\n".join([
            str(item.get("trigger", "")),
            str(item.get("lesson", "")),
            " ".join(item.get("tags", [])),
            " ".join(item.get("files", [])),
        ])
        score = score_text(query, text)
        if score >= min_score:
            h = dict(item)
            h["score"] = score
            hits.append(h)

    hits.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {"ok": True, "query": clean(query), "total": len(hits), "hits": hits[:limit], "timestamp": now_iso()}

def coding_context(query: str, limit=8) -> str:
    res = search_code_lessons(query, limit=limit, min_score=0)
    hits = res.get("hits", [])
    if not hits: return ""
    lines = ["Μόνιμα μαθήματα κώδικα που πρέπει να εφαρμόσεις:"]
    for h in hits[:limit]:
        lines.append(f"• [{h.get('severity', 'medium')}] {h.get('lesson')}")
    return "\n".join(lines)



def dedupe_code_lessons() -> dict:
    with _store_lock(CODE_LESSONS_FILE):
        return _dedupe_code_lessons_locked()


def _dedupe_code_lessons_locked() -> dict:
    lessons = load_json(CODE_LESSONS_FILE, [])
    if not isinstance(lessons, list):
        lessons = []

    seen = set()
    clean_lessons = []

    for item in lessons:
        if not isinstance(item, dict):
            continue

        key = clean(item.get("lesson", "")).lower()
        key = key.replace("μεγάλες εντολές copy-paste", "μεγάλες copy-paste εντολές")
        key = key.replace("μικρές σταθερές", "σταθερές")
        key = key.replace("αντίστοιχη explicit command", "explicit command")

        if key in seen:
            continue

        seen.add(key)
        clean_lessons.append(item)

    save_json(CODE_LESSONS_FILE, clean_lessons[:1000])
    return {"ok": True, "before": len(lessons), "after": len(clean_lessons), "removed": len(lessons) - len(clean_lessons)}


def status():
    seed_code_lessons()
    dedupe_code_lessons()
    knowledge = load_json(KNOWLEDGE_FILE, [])
    lessons = load_json(CODE_LESSONS_FILE, [])
    return {
        "ok": True,
        "tool": "Knowledge Memory Engine",
        "knowledge_items": len(knowledge) if isinstance(knowledge, list) else 0,
        "code_lessons": len(lessons) if isinstance(lessons, list) else 0,
        "knowledge_file": str(KNOWLEDGE_FILE),
        "code_lessons_file": str(CODE_LESSONS_FILE),
        "timestamp": now_iso(),
    }

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(json.dumps(status(), indent=2, ensure_ascii=False))
    elif cmd == "search":
        print(json.dumps(search_knowledge(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
    elif cmd == "answer":
        print(json.dumps(answer_from_knowledge_memory(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
    elif cmd == "code":
        print(coding_context(" ".join(sys.argv[2:])))
    else:
        print(json.dumps({"ok": False, "error": "unknown_command"}, indent=2, ensure_ascii=False))
