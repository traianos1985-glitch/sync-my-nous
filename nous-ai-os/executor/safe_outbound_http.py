"""Public-only outbound HTTP fetches with DNS pinning and bounded responses.

This module deliberately bypasses environment HTTP proxies: the validated public IP
is the address used for the TCP connection, preventing a second DNS lookup (and
DNS-rebinding TOCTOU) between validation and connect.
"""
from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from typing import Any
from urllib.parse import urlsplit

_ALLOWED_PORTS = {80, 443}
_DEFAULT_MAX_BYTES = 1_500_000


def _resolve_public_addresses(host: str, port: int) -> list[str]:
    try:
        address = ipaddress.ip_address(host)
        addresses = [address]
    except ValueError:
        try:
            records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as error:
            raise ValueError("host_resolution_failed") from error
        addresses = []
        for record in records:
            try:
                addresses.append(ipaddress.ip_address(record[4][0]))
            except ValueError as error:
                raise ValueError("host_resolution_failed") from error

    unique = list(dict.fromkeys(addresses))
    if not unique:
        raise ValueError("host_resolution_failed")
    if any(not address.is_global for address in unique):
        raise ValueError("non_public_host")
    return [str(address) for address in unique]


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to a validated IP while retaining the original TLS hostname/SNI."""

    def __init__(self, address: str, port: int, hostname: str, timeout: float):
        super().__init__(
            host=address,
            port=port,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
        self._tls_hostname = hostname

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self.host, self.port), self.timeout, self.source_address
        )
        self.sock = self._context.wrap_socket(
            self.sock, server_hostname=self._tls_hostname
        )


def fetch_public_http(
    url: str,
    *,
    timeout: float = 12.0,
    max_bytes: int = _DEFAULT_MAX_BYTES,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Fetch one public HTTP(S) resource; redirects and oversized bodies are rejected."""
    if not isinstance(url, str) or not url.strip() or len(url) > 4096:
        return {"ok": False, "error": "invalid_url"}
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        return {"ok": False, "error": "invalid_timeout"}
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        return {"ok": False, "error": "invalid_response_limit"}

    try:
        parsed = urlsplit(url.strip())
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"} or not parsed.hostname:
            return {"ok": False, "error": "unsupported_scheme"}
        if parsed.username is not None or parsed.password is not None:
            return {"ok": False, "error": "url_credentials_not_allowed"}
        port = parsed.port or (443 if scheme == "https" else 80)
        if port not in _ALLOWED_PORTS:
            return {"ok": False, "error": "blocked_port"}
        hostname = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        if (hostname == "localhost" or hostname.endswith(
            (".localhost", ".local", ".internal", ".test")
        )):
            return {"ok": False, "error": "non_public_host"}
        addresses = _resolve_public_addresses(hostname, port)
    except (ValueError, UnicodeError):
        return {"ok": False, "error": "invalid_or_non_public_url"}

    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    host_header = f"[{hostname}]" if ":" in hostname else hostname
    if port not in {80, 443}:
        host_header += f":{port}"
    request_headers = {
        "Host": host_header,
        "Connection": "close",
        "User-Agent": "NOUS-AI-OS/1.0",
        "Accept": "*/*",
    }
    if headers:
        for key, value in headers.items():
            if key.lower() not in {"host", "connection", "proxy-authorization"}:
                request_headers[str(key)] = str(value)

    last_error = "request_failed"
    for address in addresses:
        connection = None
        try:
            if scheme == "https":
                connection = _PinnedHTTPSConnection(address, port, hostname, float(timeout))
            else:
                connection = http.client.HTTPConnection(address, port, timeout=float(timeout))
            connection.request("GET", path, headers=request_headers)
            response = connection.getresponse()
            status = int(response.status)
            response_headers = {key: value for key, value in response.getheaders()}

            if 300 <= status < 400:
                response.close()
                return {
                    "ok": False, "error": "redirect_blocked", "status": status,
                    "headers": response_headers,
                }
            if status >= 400:
                response.close()
                return {
                    "ok": False, "error": "http_error", "status": status,
                    "headers": response_headers,
                }
            content_length = response.getheader("Content-Length")
            if content_length:
                try:
                    if int(content_length) > max_bytes:
                        response.close()
                        return {"ok": False, "error": "response_too_large", "status": status}
                except ValueError:
                    pass

            chunks = []
            total = 0
            while True:
                chunk = response.read(min(16_384, max_bytes + 1 - total))
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    response.close()
                    return {"ok": False, "error": "response_too_large", "status": status}
                chunks.append(chunk)
            response.close()
            return {
                "ok": True,
                "status": status,
                "headers": response_headers,
                "body": b"".join(chunks),
                "connected_ip": address,
            }
        except (OSError, http.client.HTTPException, ssl.SSLError, TimeoutError):
            last_error = "request_failed"
        finally:
            if connection is not None:
                connection.close()

    return {"ok": False, "error": last_error}


def decode_response_body(body: bytes, content_type: str = "") -> str:
    """Decode response text using its declared charset with a safe UTF-8 fallback."""
    charset = "utf-8"
    for part in str(content_type or "").split(";")[1:]:
        key, _, value = part.strip().partition("=")
        if key.lower() == "charset" and value.strip():
            charset = value.strip().strip('"')
            break
    try:
        return body.decode(charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")
