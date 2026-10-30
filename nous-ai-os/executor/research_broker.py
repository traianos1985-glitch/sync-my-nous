"""Read-only research primitives for missions and tasks.

No arbitrary commands, writes, uploads, or package installation are exposed here.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse


ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443}


@dataclass(frozen=True)
class ResearchSource:
    title: str
    url: str
    content: str = ""


def validate_url(value: str, official_domains: set[str] | None = None) -> str:
    """Validate a public web URL and fail closed on ambiguous or unresolved DNS."""
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise ValueError("invalid_url")
    try:
        parsed = urlparse(value.strip())
        port = parsed.port
    except ValueError as error:
        raise ValueError("invalid_url") from error
    if parsed.scheme.lower() not in ALLOWED_SCHEMES or not parsed.hostname:
        raise ValueError("unsupported_url")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("url_credentials_not_allowed")
    if port is not None and port not in ALLOWED_PORTS:
        raise ValueError("port_not_allowed")
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".test")):
        raise ValueError("private_host")
    if host == "metadata.google.internal":
        raise ValueError("private_host")
    if official_domains and not any(
        host == domain.lower().rstrip(".") or host.endswith("." + domain.lower().rstrip("."))
        for domain in official_domains
    ):
        raise ValueError("domain_not_allowed")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        try:
            records = socket.getaddrinfo(
                host, port or (443 if parsed.scheme.lower() == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except OSError as error:
            raise ValueError("host_resolution_failed") from error
        addresses = {ipaddress.ip_address(result[4][0]) for result in records}
        if not addresses:
            raise ValueError("host_resolution_failed")
    else:
        addresses = {address}
    if any(not address.is_global for address in addresses):
        raise ValueError("private_address")
    return parsed.geturl()


def format_context(sources: list[ResearchSource], limit: int = 12000) -> str:
    blocks = [f"[Source {index}] {source.title} ({source.url})\n{source.content[:6000]}" for index, source in enumerate(sources, 1)]
    return "\n\n".join(blocks)[:limit]


def research_status(sources: list[ResearchSource], mode: str = "auto") -> dict:
    return {"mode": mode, "used": bool(sources), "source_count": len(sources), "context": format_context(sources)}
