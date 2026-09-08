from __future__ import annotations
import json, shutil
from datetime import datetime, timezone
from pathlib import Path

def module_ok(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False

def chat_capabilities() -> dict:
    return {
        "ok": True,
        "tool": "NOUS Chat Capabilities",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "chat": {
            "normal_chat": True,
            "mission_only_with_explicit_command": True,
            "recent_chat_memory": Path("data/chat_memory_v3.json").exists(),
            "calculator": True,
            "url_reader": Path("executor/url_reader_engine.py").exists(),
            "internet_search": Path("executor/internet_search_engine.py").exists(),
        },
        "documents": {
            "txt_md_json_csv_code": True,
            "pdf_text_extraction": module_ok("pypdf"),
            "docx_text_extraction": module_ok("docx"),
            "document_chunks": Path("data/document_chunks.json").exists(),
            "document_index": Path("data/document_index.json").exists(),
        },
        "uploads": {
            "upload_engine": Path("executor/upload_processing_engine.py").exists(),
            "upload_dir": "data/document_uploads",
            "library_dir": "data/document_library",
        },
        "images": {
            "image_files_supported": True,
            "pillow": module_ok("PIL"),
            "pytesseract_module": module_ok("pytesseract"),
            "tesseract_binary": shutil.which("tesseract") is not None,
            "real_vision_understanding": False,
            "mode": "OCR only",
        },
    }

def capability_text() -> str:
    c = chat_capabilities()
    d = c["documents"]
    i = c["images"]

    return "\n".join([
        "Οι δυνατότητες του chat του ΝΟΥΣ τώρα είναι:",
        "",
        "• Κανονική συζήτηση τύπου ChatGPT.",
        "• Ανάγνωση και απαντήσεις από μαθημένα έγγραφα.",
        "• Upload & Learn για αρχεία.",
        "• Internet search όταν το ζητάς.",
        "• Άνοιγμα και περίληψη URL.",
        "• Απλοί υπολογισμοί.",
        "• Πρόσφατη μνήμη συνομιλίας.",
        "",
        "Αρχεία:",
        f"• PDF text extraction: {d['pdf_text_extraction']}",
        f"• DOCX extraction: {d['docx_text_extraction']}",
        "• TXT/MD/JSON/CSV/code: True",
        "",
        "Εικόνες:",
        f"• Pillow: {i['pillow']}",
        f"• pytesseract module: {i['pytesseract_module']}",
        f"• tesseract binary: {i['tesseract_binary']}",
        "• Πραγματική οπτική κατανόηση εικόνας: False",
        "",
        "Σημαντικό: εικόνες και scanned PDFs διαβάζονται μόνο με OCR όταν υπάρχει κείμενο."
    ])

if __name__ == "__main__":
    print(json.dumps(chat_capabilities(), indent=2, ensure_ascii=False))
