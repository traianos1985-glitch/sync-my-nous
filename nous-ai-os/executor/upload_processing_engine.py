from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from executor.document_intelligence_engine import learn_file

UPLOADS = Path("data/document_uploads")
REPORTS = Path("data/reports")

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def safe_name(name: str) -> str:
    out = "".join(ch if ch.isalnum() or ch in ".-_ " else "_" for ch in name).strip()
    return out or "upload.bin"

def process_uploaded_file(source_path: str | Path, original_name: str = "", note: str = "") -> dict[str, Any]:
    UPLOADS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    src = Path(source_path)
    if not src.exists():
        return {"ok": False, "error": "file_not_found", "path": str(src)}

    target = UPLOADS / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name(original_name or src.name)}"

    if src.resolve() != target.resolve():
        shutil.copy2(src, target)

    learned = learn_file(str(target), note=note or "uploaded_file")

    answer = "Το αρχείο ανέβηκε και περάστηκε στη μνήμη εγγράφων."
    if learned.get("ok"):
        answer += (
            f"\n\nΈγγραφο: {learned.get('name')}"
            f"\nText extracted: {learned.get('text_extracted')}"
            f"\nChunks: {learned.get('chunks')}"
        )
    else:
        answer = "Το αρχείο αποθηκεύτηκε, αλλά δεν αναλύθηκε σωστά."

    result = {
        "ok": bool(learned.get("ok")),
        "tool": "Upload Processing Engine",
        "timestamp": now_iso(),
        "stored_upload": str(target),
        "original_name": original_name or src.name,
        "answer": answer,
        "learned": learned,
    }

    report_path = REPORTS / f"upload_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, result)
    result["report_path"] = str(report_path)

    return result

def upload_status():
    UPLOADS.mkdir(parents=True, exist_ok=True)
    files = [p for p in UPLOADS.iterdir() if p.is_file()]
    return {
        "ok": True,
        "tool": "Upload Processing Engine",
        "uploads": len(files),
        "upload_dir": str(UPLOADS),
        "recent": [str(p) for p in files[-10:]],
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps(upload_status(), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(process_uploaded_file(sys.argv[1], note=" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
