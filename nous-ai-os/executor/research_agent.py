import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

HEADERS = {"User-Agent": "Mozilla/5.0 NOUS-AI-OS"}

def web_search(query):
    url = "https://duckduckgo.com/html/?q=" + quote_plus(query)
    r = requests.get(url, headers=HEADERS, timeout=15)
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

    return {"query": query, "results": results}

def fetch_page(url):
    if not url.startswith("http"):
        return {"error": "invalid_url"}

    r = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)
    return {"url": url, "content": text[:6000]}

def research(query):
    return web_search(query)
