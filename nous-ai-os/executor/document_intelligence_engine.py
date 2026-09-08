from __future__ import annotations

import json, re, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
DOCS = DATA / "document_library"
REPORTS = DATA / "reports"
INDEX = DATA / "document_index.json"
CHUNKS = DATA / "document_chunks.json"
MEMORY = DATA / "memory.json"
KNOWLEDGE = DATA / "knowledge_queue.json"

TEXT_EXTS = {".txt", ".md", ".json", ".csv", ".py", ".html", ".css", ".js"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


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


def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_pdf(path: Path):
    try:
        from pypdf import PdfReader
        r = PdfReader(str(path))
        pages = []
        for i, page in enumerate(r.pages):
            pages.append(f"\n[PAGE {i+1}]\n" + (page.extract_text() or ""))
        return "\n".join(pages), "pypdf"
    except Exception as e:
        return "", f"pdf_failed:{e!r}"


def extract_docx(path: Path):
    try:
        import docx
        d = docx.Document(str(path))
        return "\n".join(p.text for p in d.paragraphs), "python-docx"
    except Exception as e:
        return "", f"docx_failed:{e!r}"


def extract_image_ocr(path: Path):
    try:
        from PIL import Image
        import pytesseract
        text = pytesseract.image_to_string(Image.open(path), lang="eng")
        return text, "pytesseract"
    except Exception as e:
        return "", f"ocr_unavailable_or_failed:{e!r}"


def extract_text(path: Path):
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return path.read_text(encoding="utf-8", errors="replace"), "plain_text"
    if ext == ".pdf":
        return extract_pdf(path)
    if ext == ".docx":
        return extract_docx(path)
    if ext in IMAGE_EXTS:
        return extract_image_ocr(path)
    return "", "unsupported_stored_only"


def tokenize(s: str):
    return [x for x in re.findall(r"[A-Za-zΑ-Ωα-ω0-9_]{3,}", s.lower())]


def make_chunks(text: str, size=1800, overlap=250):
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        part = text[i:i+size].strip()
        if part:
            chunks.append(part)
        i += max(1, size - overlap)
    return chunks


def summarize(text: str):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    words = tokenize(text)
    freq = {}
    for w in words:
        if len(w) >= 5:
            freq[w] = freq.get(w, 0) + 1
    keywords = [k for k, _ in sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:40]]
    return {
        "chars": len(text),
        "words": len(words),
        "lines": len(lines),
        "sample": "\n".join(lines[:40])[:10000],
        "keywords": keywords,
    }


def remember_document(doc):
    memory = load_json(MEMORY, [])
    if not isinstance(memory, list):
        memory = []
    if not any(isinstance(x, dict) and x.get("document_hash") == doc["sha256"] for x in memory):
        memory.append({
            "id": int(datetime.now().timestamp() * 1000000),
            "created_at": now_iso(),
            "source": "document_intelligence_engine",
            "type": "learned_document",
            "title": doc["name"],
            "document_hash": doc["sha256"],
            "summary": doc["summary"],
            "instruction": "Use this document as a knowledge source for future answers.",
        })
        save_json(MEMORY, memory)

    knowledge = load_json(KNOWLEDGE, [])
    if not isinstance(knowledge, list):
        knowledge = []
    if not any(isinstance(x, dict) and x.get("document_hash") == doc["sha256"] for x in knowledge):
        knowledge.append({
            "id": int(datetime.now().timestamp() * 1000000),
            "created_at": now_iso(),
            "source": "document_intelligence_engine",
            "kind": "learned_document",
            "title": doc["name"],
            "document_hash": doc["sha256"],
            "summary": doc["summary"],
        })
        save_json(KNOWLEDGE, knowledge)


def learn_file(source: str, note: str = ""):
    DOCS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    src = Path(source)
    if not src.exists():
        return {"ok": False, "error": "file_not_found", "source": source}

    digest = sha256_file(src)
    stored = DOCS / f"{digest[:16]}_{src.name}"
    if not stored.exists():
        shutil.copy2(src, stored)

    text, method = extract_text(stored)
    chunks = make_chunks(text)

    doc = {
        "ok": True,
        "id": digest[:16],
        "name": src.name,
        "sha256": digest,
        "stored_path": str(stored),
        "extension": src.suffix.lower(),
        "learned_at": now_iso(),
        "note": note,
        "extract_method": method,
        "text_extracted": bool(text),
        "chunks": len(chunks),
        "summary": summarize(text) if text else {
            "chars": 0,
            "words": 0,
            "lines": 0,
            "sample": "",
            "keywords": [],
            "note": "No text extracted. For scanned Greek PDFs/images install OCR language packs later.",
        },
    }

    index = load_json(INDEX, [])
    if not isinstance(index, list):
        index = []
    index = [x for x in index if not (isinstance(x, dict) and x.get("sha256") == digest)]
    index.append(doc)
    save_json(INDEX, index)

    all_chunks = load_json(CHUNKS, [])
    if not isinstance(all_chunks, list):
        all_chunks = []
    all_chunks = [c for c in all_chunks if not (isinstance(c, dict) and c.get("document_hash") == digest)]

    for i, chunk in enumerate(chunks):
        all_chunks.append({
            "id": f"{digest[:16]}:{i}",
            "document_id": digest[:16],
            "document_hash": digest,
            "document_name": src.name,
            "chunk_index": i,
            "text": chunk,
            "tokens": tokenize(chunk),
        })

    save_json(CHUNKS, all_chunks)
    remember_document(doc)

    report_path = REPORTS / f"document_learning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, doc)
    doc["report_path"] = str(report_path)
    return doc

def answer_from_documents(question: str, limit=6):
    q_tokens = set(tokenize(question))
    chunks = load_json(CHUNKS, [])
    if not isinstance(chunks, list):
        chunks = []

    scored = []
    for c in chunks:
        if not isinstance(c, dict):
            continue
        ctokens = set(c.get("tokens", []))
        score = len(q_tokens & ctokens)
        text_low = c.get("text", "").lower()
        for word in q_tokens:
            if word in text_low:
                score += 2
        if score > 0:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [c for _, c in scored[:limit]]

    if not hits:
        return {
            "ok": True,
            "question": question,
            "answer": "Δεν βρήκα σχετική πληροφορία στα μαθημένα έγγραφα.",
            "sources": [],
        }

    return {
        "ok": True,
        "question": question,
        "answer": "Βρήκα σχετικά αποσπάσματα στα μαθημένα έγγραφα.",
        "sources": [
            {
                "document": h.get("document_name"),
                "chunk": h.get("chunk_index"),
                "excerpt": h.get("text", "")[:1500],
            }
            for h in hits
        ],
    }


def status():
    index = load_json(INDEX, [])
    chunks = load_json(CHUNKS, [])
    return {
        "tool": "Document Intelligence Engine",
        "timestamp": now_iso(),
        "documents": len(index) if isinstance(index, list) else 0,
        "chunks": len(chunks) if isinstance(chunks, list) else 0,
        "pdf_supported": True,
        "docx_supported": True,
        "image_ocr_supported_if_tesseract_available": True,
        "index": str(INDEX),
        "chunks_file": str(CHUNKS),
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2, ensure_ascii=False))
