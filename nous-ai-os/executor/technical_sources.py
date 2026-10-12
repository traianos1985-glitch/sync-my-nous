"""Read-only watcher for release metadata from a curated set of official projects.

Release notes are untrusted reference text. This module stores bounded metadata only;
it never executes release text, follows redirects, accepts caller-provided URLs, or
modifies source code or dependencies.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import re
import threading
import time
from pathlib import Path

import requests

DATA_DIR = Path(os.environ.get("NOUS_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
REPORT_PATH = DATA_DIR / "technical_sources_report.json"
HISTORY_PATH = DATA_DIR / "technical_sources_history.json"
MAX_RESPONSE_BYTES = 1_000_000
MAX_RELEASES_PER_SOURCE = 3
MAX_SOURCES = 8
_TIMEOUT = (3, 6)
_LOCK = threading.RLock()
_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "NOUS-Official-Release-Watch/1.0 (read-only)",
    "X-GitHub-Api-Version": "2022-11-28",
}
# Static allowlist: only official upstream repositories on api.github.com.
OFFICIAL_SOURCES = (
    {"name": "Python", "repository": "python/cpython", "url": "https://github.com/python/cpython/releases"},
    {"name": "Flask", "repository": "pallets/flask", "url": "https://github.com/pallets/flask/releases"},
    {"name": "Requests", "repository": "psf/requests", "url": "https://github.com/psf/requests/releases"},
    {"name": "Vite", "repository": "vitejs/vite", "url": "https://github.com/vitejs/vite/releases"},
    {"name": "Next.js", "repository": "vercel/next.js", "url": "https://github.com/vercel/next.js/releases"},
)


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def _atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _safe_excerpt(value) -> str:
    if not isinstance(value, str):
        return ""
    # Keep plain bounded text; never interpret Markdown, HTML, or embedded instructions.
    text = re.sub(r"<[^>]{0,500}>", " ", value)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:700]


def _bounded_response(response: requests.Response):
    length = response.headers.get("Content-Length", "")
    if length.isdigit() and int(length) > MAX_RESPONSE_BYTES:
        raise ValueError("source_response_too_large")
    chunks = []
    total = 0
    for chunk in response.iter_content(chunk_size=16_384):
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_RESPONSE_BYTES:
            raise ValueError("source_response_too_large")
        chunks.append(chunk)
    value = json.loads(b"".join(chunks).decode("utf-8"))
    if not isinstance(value, list):
        raise ValueError("invalid_release_payload")
    return value


def _fetch_source(source: dict) -> dict:
    repository = source.get("repository", "")
    # Validate the exact static repository shape before constructing the fixed-host URL.
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        return {"ok": False, "source": source.get("name", "unknown"), "error": "invalid_source"}
    url = f"https://api.github.com/repos/{repository}/releases?per_page={MAX_RELEASES_PER_SOURCE}"
    response = None
    try:
        response = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, allow_redirects=False, stream=True)
        if response.status_code != 200:
            return {"ok": False, "source": source["name"], "error": f"source_http_{response.status_code}"}
        releases = _bounded_response(response)
        items = []
        for release in releases[:MAX_RELEASES_PER_SOURCE]:
            if not isinstance(release, dict) or release.get("draft") is True:
                continue
            tag = release.get("tag_name")
            if not isinstance(tag, str) or not tag.strip():
                continue
            html_url = release.get("html_url")
            # Never surface arbitrary response URLs as clickable sources.
            if not isinstance(html_url, str) or not html_url.startswith(source["url"] + "/"):
                html_url = source["url"]
            items.append({
                "project": source["name"],
                "repository": repository,
                "tag": tag[:100],
                "name": _safe_excerpt(release.get("name") or tag)[:180],
                "published_at": str(release.get("published_at") or "")[:40],
                "url": html_url,
                "notes_excerpt": _safe_excerpt(release.get("body")),
                "notes_are_untrusted_data": True,
                "action": "review_only",
            })
        return {"ok": True, "source": source["name"], "repository": repository, "release_count": len(items), "releases": items}
    except (requests.RequestException, ValueError, UnicodeDecodeError) as exc:
        reason = str(exc)[:120] if str(exc) else type(exc).__name__
        return {"ok": False, "source": source.get("name", "unknown"), "error": reason}
    finally:
        if response is not None:
            response.close()


def run_source_scan() -> dict:
    """Fetch only allowlisted official release metadata and persist a bounded report."""
    with _LOCK:
        sources = list(OFFICIAL_SOURCES[:MAX_SOURCES])
        # Query official sources concurrently. Sequential 3–9 second network
        # waits can exceed hosted-platform request windows and look like a cold
        # start even when the process is healthy.
        results_by_index = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(sources) or 1)) as pool:
            futures = {
                pool.submit(_fetch_source, source): index
                for index, source in enumerate(sources)
            }
            for future in concurrent.futures.as_completed(futures):
                index = futures[future]
                try:
                    results_by_index[index] = future.result()
                except Exception as exc:
                    results_by_index[index] = {
                        "ok": False,
                        "source": sources[index].get("name", "unknown"),
                        "error": type(exc).__name__,
                    }
        results = [
            results_by_index.get(index, {
                "ok": False,
                "source": source.get("name", "unknown"),
                "error": "source_result_missing",
            })
            for index, source in enumerate(sources)
        ]
        ok_count = sum(item.get("ok") is True for item in results)
        report = {
            "ok": ok_count > 0,
            "status": "complete" if ok_count == len(results) else "partial" if ok_count else "unavailable",
            "checked_at": time.time(),
            "source_count": len(results),
            "successful_source_count": ok_count,
            "release_count": sum(item.get("release_count", 0) for item in results),
            "sources": results,
            "safety": {
                "arbitrary_urls_accepted": False,
                "redirects_followed": False,
                "release_text_executed": False,
                "source_files_modified": 0,
                "dependency_changes_performed": 0,
            },
        }
        _atomic_json(REPORT_PATH, report)
        history = _read_json(HISTORY_PATH, [])
        if not isinstance(history, list):
            history = []
        history.append({
            "checked_at": report["checked_at"],
            "status": report["status"],
            "source_count": report["source_count"],
            "successful_source_count": report["successful_source_count"],
            "release_count": report["release_count"],
        })
        _atomic_json(HISTORY_PATH, history[-30:])
        return report


def latest_source_report() -> dict:
    report = _read_json(REPORT_PATH, None)
    if not isinstance(report, dict):
        return {"ok": True, "status": "not_scanned", "source_count": len(OFFICIAL_SOURCES), "release_count": 0, "sources": []}
    return report


def source_watch_status() -> dict:
    report = latest_source_report()
    return {
        "ok": True,
        "watcher": "official_release_metadata",
        "configured_sources": [{"name": item["name"], "repository": item["repository"], "url": item["url"]} for item in OFFICIAL_SOURCES],
        "source_count": len(OFFICIAL_SOURCES),
        "last_checked_at": report.get("checked_at"),
        "last_status": report.get("status", "not_scanned"),
        "last_release_count": report.get("release_count", 0),
        "automatic_updates": False,
        "release_notes_are_untrusted_data": True,
    }
