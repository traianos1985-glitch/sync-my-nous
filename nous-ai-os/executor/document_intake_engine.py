from __future__ import annotations

import json, shutil, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
DOCS = DATA / "document_library"
UPLOADS = DATA / "document_uploads"
REPORTS = DATA / "reports"
KNOWLEDGE = DATA / "knowledge_queue.json"
MEMORY = DATA / "memory.json"
INDEX = DATA / "document_index.json"

TEXT_EXTS = {".txt", ".md", ".json", ".csv", ".py", ".html", ".css", ".js"}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text_file(path: Path, limit=250000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def read_pdf(path: Path, limit=250000) -> tuple[str, str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages[:80]:
            pages.append(page.extract_text() or "")
        return ("\n".join(pages)[:limit], "pypdf")
    except Exception as e:
        return ("", f"pdf_extract_failed: {e!r}")


def read_docx(path: Path, limit=250000) -> tuple[str, str]:
    try:
        import docx
        d = docx.Document(str(path))
        text = "\n".join(p.text for p in d.paragraphs)
        return (text[:limit], "python-docx")
    except Exception as e:
        return ("", f"docx_extract_failed: {e!r}")


def extract_text(path: Path) -> tuple[str, str]:
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return read_text_file(path), "plain_text"
    if ext == ".pdf":
        return read_pdf(path)
    if ext == ".docx":
        return read_docx(path)
    return "", "stored_only"


def summarize_text(text: str) -> dict[str, Any]:
    words = text.split()
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    sample = "\n".join(lines[:35])
    keywords = []
    for token in words:
        t = token.strip(".,;:!?()[]{}<>\"'").lower()
        if len(t) >= 6 and t not in keywords:
            keywords.append(t)
        if len(keywords) >= 50:
            break
    return {
        "chars": len(text),
        "words": len(words),
        "lines": len(lines),
        "sample": sample[:8000],
        "keywords": keywords,
    }


def add_memory(doc: dict[str, Any]) -> None:
    memory = load_json(MEMORY, [])
    if not isinstance(memory, list):
        memory = []
    if any(isinstance(x, dict) and x.get("document_hash") == doc.get("sha256") for x in memory):
        return
    memory.append({
        "id": int(datetime.now().timestamp() * 1000000),
        "created_at": now_iso(),
        "source": "document_intake_engine",
        "type": "document_memory",
        "title": doc.get("name"),
        "document_hash": doc.get("sha256"),
        "summary": doc.get("summary"),
        "path": doc.get("stored_path"),
    })
    save_json(MEMORY, memory)


def add_knowledge(doc: dict[str, Any]) -> None:
    queue = load_json(KNOWLEDGE, [])
    if not isinstance(queue, list):
        queue = []
    if any(isinstance(x, dict) and x.get("document_hash") == doc.get("sha256") for x in queue):
        return
    queue.append({
        "id": int(datetime.now().timestamp() * 1000000),
        "created_at": now_iso(),
        "source": "document_intake_engine",
        "kind": "document",
        "title": doc.get("name"),
        "document_hash": doc.get("sha256"),
        "summary": doc.get("summary"),
        "path": doc.get("stored_path"),
    })
    save_json(KNOWLEDGE, queue)


def ingest_file(source: str | Path, note: str = "") -> dict[str, Any]:
    DOCS.mkdir(parents=True, exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    src = Path(source)
    if not src.exists():
        return {"ok": False, "error": "file_not_found", "source": str(src)}

    digest = sha256_file(src)
    stored = DOCS / f"{digest[:16]}_{src.name}"
    if not stored.exists():
        shutil.copy2(src, stored)

    text, method = extract_text(stored)
    summary = summarize_text(text) if text else {
        "chars": 0,
        "words": 0,
        "lines": 0,
        "sample": "",
        "keywords": [],
        "note": "Stored, but no text extracted yet.",
    }

    doc = {
        "ok": True,
        "id": digest[:16],
        "name": src.name,
        "extension": src.suffix.lower(),
        "sha256": digest,
        "stored_path": str(stored),
        "ingested_at": now_iso(),
        "note": note,
        "extract_method": method,
        "summary": summary,
        "capabilities": {
            "text_indexed": bool(text),
            "pdf_text_extraction": src.suffix.lower() == ".pdf" and bool(text),
            "docx_text_extraction": src.suffix.lower() == ".docx" and bool(text),
            "image_ocr": False,
            "stored_for_future_processing": True,
        },
    }

    index = load_json(INDEX, [])
    if not isinstance(index, list):
        index = []

    existing = next((x for x in index if isinstance(x, dict) and x.get("sha256") == digest), None)
    if existing:
        existing.update(doc)
    else:
        index.append(doc)

    save_json(INDEX, index)
    add_memory(doc)
    add_knowledge(doc)

    report_path = REPORTS / f"document_intake_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, doc)
    doc["report_path"] = str(report_path)
    return doc


def search_documents(query: str) -> dict[str, Any]:
    q = query.lower().strip()
    index = load_json(INDEX, [])
    if not isinstance(index, list):
        index = []
    hits = []
    for doc in index:
        if isinstance(doc, dict) and q in json.dumps(doc, ensure_ascii=False).lower():
            hits.append(doc)
    return {"ok": True, "query": query, "total": len(hits), "hits": hits[:20]}


def run_document_intake_status() -> dict[str, Any]:
    index = load_json(INDEX, [])
    if not isinstance(index, list):
        index = []
    return {
        "tool": "Document Intake Engine",
        "timestamp": now_iso(),
        "documents": len(index),
        "text_indexed": len([x for x in index if isinstance(x, dict) and x.get("capabilities", {}).get("text_indexed")]),
        "stored_only": len([x for x in index if isinstance(x, dict) and not x.get("capabilities", {}).get("text_indexed")]),
        "pdf_supported": True,
        "docx_supported": True,
        "image_ocr_supported": False,
        "index_path": str(INDEX),
        "library_path": str(DOCS),
    }


if __name__ == "__main__":
    print(json.dumps(run_document_intake_status(), indent=2, ensure_ascii=False))
