from executor.internet import fetch

def web_command(text):
    parts = text.split(" ", 1)

    if len(parts) < 2:
        return {"error": "usage: web https://example.com"}

    url = parts[1].strip()
    return fetch(url)
