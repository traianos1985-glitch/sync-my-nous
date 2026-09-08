from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from executor.internet_search_engine import search_web
from executor.url_reader_engine import read_url

REPORTS = Path("data/reports")
CACHE = Path("data/deep_research_cache.json")


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


def clean_line(s: str) -> str:
    return " ".join(str(s or "").split()).strip()


def make_bullets(text: str, max_lines: int = 4) -> list[str]:
    lines = [clean_line(x) for x in text.splitlines() if clean_line(x)]
    useful = []
    for line in lines:
        if len(line) < 60:
            continue
        if line in useful:
            continue
        useful.append(line[:320])
        if len(useful) >= max_lines:
            break
    return useful


def deep_research(query: str, max_results: int = 5) -> dict[str, Any]:
    query = clean_line(query)
    if not query:
        return {"ok": False, "error": "empty_query"}

    search = search_web(query, limit=max_results)

    if not search.get("ok"):
        return {
            "ok": False,
            "tool": "Deep Research Engine",
            "query": query,
            "error": search.get("error"),
            "raw": search,
        }

    results = search.get("results", [])[:max_results]
    pages = []

    for r in results:
        url = r.get("url")
        if not url:
            continue

        page = read_url(url, limit=9000)
        if page.get("ok"):
            bullets = make_bullets(page.get("text", ""), 4)
            pages.append({
                "title": page.get("title") or r.get("title"),
                "url": url,
                "domain": page.get("domain"),
                "bullets": bullets,
                "chars": page.get("chars", 0),
            })
        else:
            pages.append({
                "title": r.get("title"),
                "url": url,
                "domain": "",
                "bullets": [r.get("snippet", "")] if r.get("snippet") else [],
                "error": page.get("error"),
            })

    answer_lines = [
        f"Έκανα βαθύτερη έρευνα για: {query}",
        "",
        "Σύνοψη:"
    ]

    used_sources = []

    for i, p in enumerate(pages[:5], 1):
        title = p.get("title") or "Πηγή"
        url = p.get("url")
        used_sources.append({"title": title, "url": url})

        answer_lines.append("")
        answer_lines.append(f"{i}. {title}")

        bullets = p.get("bullets") or []
        if not bullets:
            answer_lines.append("• Δεν βρέθηκε αρκετό καθαρό κείμενο από αυτή την πηγή.")
        else:
            for b in bullets[:3]:
                answer_lines.append(f"• {b}")

    answer_lines.append("")
    answer_lines.append("Πηγές:")
    for i, s in enumerate(used_sources, 1):
        answer_lines.append(f"[{i}] {s.get('title')} — {s.get('url')}")

    payload = {
        "ok": True,
        "tool": "Deep Research Engine",
        "timestamp": now_iso(),
        "query": query,
        "answer": "\n".join(answer_lines),
        "sources": used_sources,
        "pages": pages,
        "raw_search": {
            "results_count": len(results),
        },
    }

    cache = load_json(CACHE, [])
    if not isinstance(cache, list):
        cache = []
    cache.append({
        "timestamp": payload["timestamp"],
        "query": query,
        "sources": used_sources,
    })
    save_json(CACHE, cache[-100:])

    report = REPORTS / f"deep_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report, payload)
    payload["report_path"] = str(report)

    return payload


if __name__ == "__main__":
    import sys
    print(json.dumps(deep_research(" ".join(sys.argv[1:])), indent=2, ensure_ascii=False))
