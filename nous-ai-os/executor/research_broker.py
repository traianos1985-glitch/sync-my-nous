"""Read-only research primitives for missions and tasks.

No arbitrary commands, writes, uploads, or package installation are exposed here.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse


ALLOWED_SCHEMES = {"http", "https"}


@dataclass(frozen=True)
class ResearchSource:
    title: str
    url: str
    content: str = ""


def validate_url(value: str, official_domains: set[str] | None = None) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.hostname:
        raise ValueError("unsupported_url")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".localhost") or host == "metadata.google.internal":
        raise ValueError("private_host")
    try:
        address = ipaddress.ip_address(host)
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            raise ValueError("private_address")
    except ValueError as error:
        if str(error) == "private_address":
            raise
    if official_domains and not any(host == domain or host.endswith("." + domain) for domain in official_domains):
        raise ValueError("domain_not_allowed")
    for result in socket.getaddrinfo(host, None):
        address = ipaddress.ip_address(result[4][0])
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            raise ValueError("private_address")
    return parsed.geturl()


def format_context(sources: list[ResearchSource], limit: int = 12000) -> str:
    blocks = [f"[Source {index}] {source.title} ({source.url})\n{source.content[:6000]}" for index, source in enumerate(sources, 1)]
    return "\n\n".join(blocks)[:limit]


def research_status(sources: list[ResearchSource], mode: str = "auto") -> dict:
    return {"mode": mode, "used": bool(sources), "source_count": len(sources), "context": format_context(sources)}
