import requests

def fetch(url):

    try:

        r = requests.get(
            url,
            timeout=10
        )

        return {
            "status": r.status_code,
            "text": r.text[:3000]
        }

    except Exception as e:

        return {
            "error": str(e)
        }
