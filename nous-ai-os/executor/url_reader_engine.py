"""Safe, bounded HTTP page reader used by NOUS web research."""
from __future__ import annotations

import ipaddress
import json
import socket
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CACHE = Path("data/url_reader_cache.json")
REPORTS = Path("data/reports")
MAX_RESPONSE_BYTES = 1_500_000
DEFAULT_TEXT_LIMIT = 12_000
_ALLOWED_PORTS = {80, 443}


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
    return re.sub(r"\\s+", " ", text or "").strip()


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\\s]+", text or "")


def _validate_public_http_url(url: str) -> tuple[bool, str | None]:
    """Reject non-web schemes, credentials, unusual ports and non-public hosts."""
    try:
        parsed = urlparse(str(url).strip())
        if parsed.scheme.lower() not in {"http", "https"}:
            return False, "unsupported_scheme"
        if not parsed.hostname or parsed.username is not None or parsed.password is not None:
            return False, "invalid_url"
        if parsed.port is not None and parsed.port not in _ALLOWED_PORTS:
            return False, "blocked_port"

        host = parsed.hostname.rstrip(".").lower()
        if host in {"localhost"} or host.endswith((".localhost", ".local", ".internal", ".test")):
            return False, "non_public_host"

        try:
            addresses = [ipaddress.ip_address(host)]
        except ValueError:
            try:
                addresses = [
                    ipaddress.ip_address(item[4][0])
                    for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
                ]
            except (OSError, ValueError):
                return False, "host_resolution_failed"

        if not addresses or any(not address.is_global for address in addresses):
            return False, "non_public_host"
        return True, None
    except ValueError:
        return False, "invalid_url"


def read_url(url: str, limit: int = DEFAULT_TEXT_LIMIT) -> dict[str, Any]:
    """Fetch public HTML only, without following redirects or loading unbounded bodies."""
    if not isinstance(url, str) or not url.strip():
        return {"ok": False, "error": "invalid_url", "url": str(url or "")}
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        return {"ok": False, "error": "invalid_text_limit", "url": url}
    limit = min(limit, DEFAULT_TEXT_LIMIT * 4)

    safe, reason = _validate_public_http_url(url)
    if not safe:
        return {"ok": False, "error": reason or "unsafe_url", "url": url}

    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception:
        return {"ok": False, "error": "missing_dependencies", "url": url}

    response = None
    try:
        response = requests.get(
            url,
            timeout=(4, 12),
            allow_redirects=False,
            stream=True,
            headers={
                "User-Agent": "NOUS-AI-OS/1.0 (+https://github.com/traianos1985-glitch/sync-my-nous)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        if 300 <= response.status_code < 400:
            return {"ok": False, "error": "redirect_blocked", "status": response.status_code, "url": url}
        if response.status_code >= 400:
            return {"ok": False, "error": "http_error", "status": response.status_code, "url": url}

        content_type = str(response.headers.get("Content-Type", "")).lower()
        if content_type and not any(kind in content_type for kind in ("text/html", "application/xhtml+xml")):
            return {"ok": False, "error": "unsupported_content_type", "url": url}

        declared_length = response.headers.get("Content-Length")
        if declared_length:
            try:
                if int(declared_length) > MAX_RESPONSE_BYTES:
                    return {"ok": False, "error": "response_too_large", "url": url}
            except ValueError:
                pass

        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=16_384):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_RESPONSE_BYTES:
                return {"ok": False, "error": "response_too_large", "url": url}
            chunks.append(chunk)
        body = b"".join(chunks)
        encoding = response.encoding or "utf-8"
        html = body.decode(encoding, errors="replace")
    except Exception:
        return {"ok": False, "error": "request_failed", "url": url}
    finally:
        if response is not None:
            response.close()

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "object", "embed"]):
        tag.decompose()

    title = clean(soup.title.get_text(" ", strip=True)) if soup.title else url
    paragraphs = []
    for element in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = clean(element.get_text(" ", strip=True))
        if len(text) >= 40:
            paragraphs.append(text)

    page_text = "\\n".join(paragraphs)[:limit]
    result = {
        "ok": True,
        "tool": "URL Reader Engine",
        "timestamp": now_iso(),
        "url": url,
        "domain": urlparse(url).netloc,
        "title": title,
        "chars": len(page_text),
        "text": page_text,
    }

    cache = load_json(CACHE, [])
    if not isinstance(cache, list):
        cache = []
    cache.append({key: value for key, value in result.items() if key != "text"})
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
            "answer": f"Δεν μπόρεσα να διαβάσω τη σελίδα ({data.get('error', 'read_failed')}).",
            "raw": data,
        }

    lines = [line.strip() for line in data.get("text", "").splitlines() if line.strip()]
    useful = lines[:8]
    if not useful:
        answer = f"Άνοιξα τη σελίδα «{data.get('title')}», αλλά δεν βρήκα αρκετό καθαρό κείμενο."
    else:
        answer_lines = [f"Διάβασα τη σελίδα: {data.get('title')}", "", "Βασικά σημεία:"]
        for line in useful[:5]:
            if len(line) > 260:
                line = line[:260].rstrip() + "..."
            answer_lines.append(f"• {line}")
        answer_lines.extend(["", f"Πηγή: {url}"])
        answer = "\\n".join(answer_lines)

    return {
        "ok": True,
        "mode": "url_reader",
        "answer": answer,
        "url": url,
        "title": data.get("title"),
        "raw": {key: value for key, value in data.items() if key != "text"},
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(summarize_url(" ".join(sys.argv[1:])), indent=2, ensure_ascii=False))
