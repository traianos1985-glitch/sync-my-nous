import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

from executor.safe_outbound_http import decode_response_body, fetch_public_http

HEADERS = {"User-Agent": "Mozilla/5.0 NOUS-AI-OS"}

def _ddg_search(query):
    url = "https://duckduckgo.com/html/?q=" + quote_plus(query)
    r = requests.get(url, headers=HEADERS, timeout=(4, 12))
    soup = BeautifulSoup(r.text, "html.parser")

    results = []
    for a in soup.select(".result__a")[:5]:
        title = a.get_text(" ", strip=True)
        href = a.get("href")
        if href and "uddg=" in href:
            qs = parse_qs(urlparse(href).query)
            href = unquote(qs.get("uddg", [href])[0])
        if href and href.startswith("//"):
            href = "https:" + href
        results.append({"title": title, "url": href})
    return results


def web_search(query):
    try:
        results = _ddg_search(query)
    except requests.RequestException:
        results = []
    if not results:
        # DuckDuckGo blocks/times out from some hosts (e.g. Render); fall back to Wikipedia & co.
        from executor.internet_search_engine import search_web

        fallback = search_web(query).get("results", [])
        results = [
            {"title": x.get("title", ""), "url": x.get("url", ""), "snippet": x.get("snippet", "")}
            for x in fallback
        ]
    return {"query": query, "results": results}

def fetch_page(url):
    fetched = fetch_public_http(
        url,
        timeout=15,
        max_bytes=1_000_000,
        headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
    )
    if not fetched.get("ok"):
        return {"error": fetched.get("error", "request_failed")}

    content_type = str(fetched.get("headers", {}).get("Content-Type", "")).lower()
    if content_type and not any(
        kind in content_type for kind in ("text/html", "application/xhtml+xml")
    ):
        return {"error": "unsupported_content_type"}

    html = decode_response_body(fetched.get("body", b""), content_type)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)
    return {"url": url, "content": text[:6000]}

def research(query):
    return web_search(query)
