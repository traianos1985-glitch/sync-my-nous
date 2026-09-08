from executor.internet import get

def search(query):
    url = f"https://duckduckgo.com/html/?q={query}"
    return get(url)

def fetch(url):
    return get(url)
