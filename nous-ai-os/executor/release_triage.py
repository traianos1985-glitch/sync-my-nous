"""Deterministic triage of official release notes into a review-only evidence queue.

Release notes are untrusted input. This module only classifies bounded text and
returns source-linked signals; it never creates executable plans or edits code.
"""
from __future__ import annotations

import re
from typing import Any

from executor.technical_sources import OFFICIAL_SOURCES, latest_source_report

MAX_ITEMS = 25
MAX_TEXT = 700
_SIGNAL_RULES = (
    ("security", "high", re.compile(
        r"\b(security|vulnerabilit(?:y|ies)|cve-\d{4}-\d+|remote code execution|"
        r"privilege escalation|authentication bypass|security fix|security advisory)\b",
        re.IGNORECASE,
    )),
    ("breaking_change", "high", re.compile(
        r"\b(breaking change|breaking changes|backward incompatible|backwards incompatible|"
        r"removed api|removed support|migration required|deprecated api)\b",
        re.IGNORECASE,
    )),
    ("bug_fix", "normal", re.compile(
        r"\b(fix(?:es|ed)?|bugfix|bug fix|regression|crash|memory leak|incorrect result)\b",
        re.IGNORECASE,
    )),
    ("performance", "normal", re.compile(
        r"\b(performance|faster|speed(?:up| improvement)?|optimization|optimisation|"
        r"reduced memory|latency)\b",
        re.IGNORECASE,
    )),
)

_ALLOWED = {
    (source["repository"], source["url"])
    for source in OFFICIAL_SOURCES
}


def _text(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    value = re.sub(r"[\x00-\x1f\x7f]", " ", value)
    return re.sub(r"\s+", " ", value).strip()[:limit]


def _valid_release(release: Any) -> bool:
    if not isinstance(release, dict):
        return False
    repository = release.get("repository")
    url = release.get("url")
    if not isinstance(repository, str) or not isinstance(url, str):
        return False
    if not any(
        repository == allowed_repo and url.startswith(allowed_url + "/")
        for allowed_repo, allowed_url in _ALLOWED
    ):
        # The watcher uses the canonical releases URL as a safe fallback.
        return not any(
            repository == allowed_repo and url == allowed_url
            for allowed_repo, allowed_url in _ALLOWED
        )
    return True


def triage_release(release: dict) -> dict:
    """Return a deterministic classification; release text is never instructions."""
    excerpt = _text(release.get("notes_excerpt"), MAX_TEXT)
    title = _text(release.get("name") or release.get("tag"), 180)
    evidence_text = f"{title} {excerpt}"
    signals = []
    priorities = []
    for category, priority, pattern in _SIGNAL_RULES:
        matches = pattern.findall(evidence_text)
        if matches:
            signals.append(category)
            priorities.append(priority)
    priority = "high" if "high" in priorities else "normal" if priorities else "review"
    return {
        "project": _text(release.get("project"), 80),
        "repository": _text(release.get("repository"), 120),
        "release": title or _text(release.get("tag"), 100),
        "tag": _text(release.get("tag"), 100),
        "published_at": _text(release.get("published_at"), 40),
        "source_url": _text(release.get("url"), 300),
        "evidence_excerpt": excerpt,
        "signals": signals or ["manual_review"],
        "priority": priority,
        "confidence": "keyword_signal" if signals else "unclassified",
        "status": "needs_human_review",
        "action": "review_only",
        "notes_are_untrusted_data": True,
        "code_generated": False,
        "code_executed": False,
    }


def triage_latest_releases(report: dict | None = None, limit: int = MAX_ITEMS) -> dict:
    """Build a bounded review queue from the latest official-source report."""
    report = report if isinstance(report, dict) else latest_source_report()
    try:
        count = max(1, min(int(limit), MAX_ITEMS))
    except (TypeError, ValueError):
        count = MAX_ITEMS
    items = []
    seen = set()
    sources = report.get("sources", [])
    if not isinstance(sources, list):
        sources = []
    for source_result in sources:
        if not isinstance(source_result, dict) or source_result.get("ok") is not True:
            continue
        releases = source_result.get("releases", [])
        if not isinstance(releases, list):
            continue
        for release in releases:
            if not _valid_release(release):
                continue
            key = (release.get("repository"), release.get("tag"))
            if key in seen:
                continue
            seen.add(key)
            items.append(triage_release(release))
            if len(items) >= count:
                break
        if len(items) >= count:
            break
    items.sort(key=lambda item: (item["priority"] != "high", item["published_at"]), reverse=False)
    return {
        "ok": True,
        "status": report.get("status", "not_scanned"),
        "checked_at": report.get("checked_at"),
        "source_count": len(sources),
        "items_count": len(items),
        "items": items,
        "safety": {
            "release_text_executed": False,
            "upgrade_plans_created": False,
            "source_files_modified": 0,
            "requires_human_review": True,
        },
    }
