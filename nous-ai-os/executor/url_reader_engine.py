from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CACHE = Path("data/url_reader_cache.json")
REPORTS = Path("data/reports")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s]+", text or "")


def read_url(url: str, limit: int = 12000) -> dict[str, Any]:
    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception as e:
        return {"ok": False, "error": "missing_dependencies", "detail": repr(e)}

    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 NOUS"})
    except Exception as e:
        return {"ok": False, "error": "request_failed", "detail": repr(e), "url": url}

    if r.status_code >= 400:
        return {"ok": False, "error": "http_error", "status": r.status_code, "url": url}

    soup = BeautifulSoup(r.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = clean(soup.title.get_text(" ", strip=True)) if soup.title else url

    paragraphs = []
    for el in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        t = clean(el.get_text(" ", strip=True))
        if len(t) >= 40:
            paragraphs.append(t)

    text = "\n".join(paragraphs)
    text = text[:limit]

    result = {
        "ok": True,
        "tool": "URL Reader Engine",
        "timestamp": now_iso(),
        "url": url,
        "domain": urlparse(url).netloc,
        "title": title,
        "chars": len(text),
        "text": text,
    }

    cache = load_json(CACHE, [])
    if not isinstance(cache, list):
        cache = []
    cache.append({k: v for k, v in result.items() if k != "text"})
    save_json(CACHE, cache[-100:])

    report = REPORTS / f"url_reader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report, result)
    result["report_path"] = str(report)

    return result


def summarize_url(url: str) -> dict[str, Any]:
    data = read_url(url)
    if not data.get("ok"):
        return {
            "ok": False,
            "answer": f"Δεν μπόρεσα να διαβάσω τη σελίδα: {data.get('error')}",
            "raw": data,
        }

    lines = [x.strip() for x in data.get("text", "").splitlines() if x.strip()]
    useful = lines[:8]

    if not useful:
        answer = f"Άνοιξα τη σελίδα «{data.get('title')}», αλλά δεν βρήκα αρκετό καθαρό κείμενο."
    else:
        answer_lines = [
            f"Διάβασα τη σελίδα: {data.get('title')}",
            "",
            "Βασικά σημεία:"
        ]
        for line in useful[:5]:
            if len(line) > 260:
                line = line[:260].rstrip() + "..."
            answer_lines.append(f"• {line}")
        answer_lines.append("")
        answer_lines.append(f"Πηγή: {url}")
        answer = "\n".join(answer_lines)

    return {
        "ok": True,
        "mode": "url_reader",
        "answer": answer,
        "url": url,
        "title": data.get("title"),
        "raw": {k: v for k, v in data.items() if k != "text"},
    }


if __name__ == "__main__":
    import sys
    u = " ".join(sys.argv[1:])
    print(json.dumps(summarize_url(u), indent=2, ensure_ascii=False))
