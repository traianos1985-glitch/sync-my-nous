from executor.internet import fetch

def open_url(url):

    if not url.startswith("http"):
        return {
            "error":"invalid_url"
        }

    return fetch(url)
