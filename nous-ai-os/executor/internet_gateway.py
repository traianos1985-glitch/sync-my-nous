import requests
from bs4 import BeautifulSoup

SAFE_DOMAINS = [
    "example.com",
    "wikipedia.org",
    "python.org",
    "github.com"
]

TIMEOUT = 10


class InternetGateway:

    def is_allowed(self, url):

        for domain in SAFE_DOMAINS:

            if domain in url:
                return True

        return False

    def fetch(self, url):

        if not self.is_allowed(url):

            return {
                "error": "domain not allowed"
            }

        try:

            r = requests.get(
                url,
                timeout=TIMEOUT,
                headers={
                    "User-Agent": "NOUS-AI-OS"
                }
            )

            soup = BeautifulSoup(
                r.text,
                "html.parser"
            )

            text = soup.get_text()

            return {
                "success": True,
                "url": url,
                "content": text[:5000]
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }
