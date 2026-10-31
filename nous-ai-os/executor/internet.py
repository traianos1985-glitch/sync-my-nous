"""Legacy internet fetch adapter backed by the public-only pinned HTTP client."""

from executor.safe_outbound_http import decode_response_body, fetch_public_http


def fetch(url):
    result = fetch_public_http(url, timeout=10, max_bytes=1_000_000)
    if not result.get("ok"):
        return {"error": result.get("error", "request_failed")}
    content_type = str(result.get("headers", {}).get("Content-Type", ""))
    return {
        "status": result.get("status"),
        "text": decode_response_body(result.get("body", b""), content_type)[:3000],
    }
