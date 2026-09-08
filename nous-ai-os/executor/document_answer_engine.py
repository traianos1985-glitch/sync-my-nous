from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"
CHUNKS = DATA / "document_chunks.json"
INDEX = DATA / "document_index.json"
ANSWER_REPORT = DATA / "document_answer_report.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def tokenize(text: str) -> list[str]:
    return [
        x.lower()
        for x in re.findall(r"[A-Za-zΑ-Ωα-ωΆΈΉΊΌΎΏάέήίόύώϊΐϋΰ0-9_]{3,}", text or "")
    ]


def normalize_word(w: str) -> str:
    w = w.lower().strip()
    endings = [
        "σεων", "σεις", "σης", "ους", "ες", "ων", "ας", "ος", "ης", "ες", "οι", "τα", "το", "τη", "την", "στο", "στα"
    ]
    for e in endings:
        if len(w) > len(e) + 3 and w.endswith(e):
            return w[: -len(e)]
    return w


def keyword_set(text: str) -> set[str]:
    return {normalize_word(x) for x in tokenize(text) if len(normalize_word(x)) >= 3}


def score_chunk(question: str, chunk: dict[str, Any]) -> dict[str, Any]:
    q_words = keyword_set(question)
    text = str(chunk.get("text", ""))
    c_words = keyword_set(text)

    overlap = q_words & c_words
    phrase_bonus = 0
    low = text.lower()
    for raw in tokenize(question):
        if len(raw) >= 5 and raw.lower() in low:
            phrase_bonus += 2

    score = len(overlap) * 5 + phrase_bonus

    return {
        "score": score,
        "overlap": sorted(overlap),
        "chunk": chunk,
    }


def find_best_chunks(question: str, limit: int = 6) -> list[dict[str, Any]]:
    chunks = load_json(CHUNKS, [])
    if not isinstance(chunks, list):
        chunks = []

    scored = []
    for chunk in chunks:
        if isinstance(chunk, dict):
            s = score_chunk(question, chunk)
            if s["score"] > 0:
                scored.append(s)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def clean_sentence(line: str) -> str:
    line = re.sub(r"\s+", " ", line or "").strip()
    line = line.strip("•-* \t")
    return line


def split_sentences(text: str) -> list[str]:
    raw = re.split(r"(?<=[.!;;;])\s+|\n+", text or "")
    out = []
    for x in raw:
        x = clean_sentence(x)
        if not x:
            continue
        low = x.lower()
        if low.startswith("εγχειρίδιο"):
            continue
        if "δοκιμαστικό" in low and "εγχειρίδιο" in low:
            continue
        if low.endswith("εγχειρίδιο.") or low.endswith("manual."):
            continue
        if x not in out:
            out.append(x)
    return out


def synthesize_answer(question: str, scored_hits: list[dict[str, Any]]) -> dict[str, Any]:
    if not scored_hits:
        return {
            "answer": "Δεν βρήκα σχετική πληροφορία στα μαθημένα έγγραφα.",
            "sources": [],
            "confidence": "low",
        }

    q_words = keyword_set(question)
    selected_sentences = []
    sources = []

    for hit in scored_hits:
        chunk = hit["chunk"]
        text = str(chunk.get("text", ""))
        sentences = split_sentences(text)

        for sentence in sentences:
            s_words = keyword_set(sentence)
            if q_words & s_words or len(selected_sentences) < 2:
                if sentence not in selected_sentences:
                    selected_sentences.append(sentence)

        sources.append({
            "document": chunk.get("document_name"),
            "chunk": chunk.get("chunk_index"),
            "score": hit.get("score"),
            "overlap": hit.get("overlap", []),
        })

    selected_sentences = selected_sentences[:6]

    if not selected_sentences:
        selected_sentences = [
            clean_sentence(scored_hits[0]["chunk"].get("text", ""))[:700]
        ]

    intro = "Σύμφωνα με τα μαθημένα έγγραφα:"
    bullets = "\n".join("• " + s for s in selected_sentences)

    confidence = "high" if scored_hits[0].get("score", 0) >= 20 else "medium"

    return {
        "answer": intro + "\n\n" + bullets,
        "sources": sources[:5],
        "confidence": confidence,
    }


def answer_question(question: str, limit: int = 6) -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)

    hits = find_best_chunks(question, limit=limit)
    synthesized = synthesize_answer(question, hits)

    report = {
        "tool": "Document Answer Engine V2",
        "timestamp": now_iso(),
        "question": question,
        "answer": synthesized["answer"],
        "confidence": synthesized["confidence"],
        "sources": synthesized["sources"],
        "hits": [
            {
                "score": h.get("score"),
                "document": h.get("chunk", {}).get("document_name"),
                "chunk": h.get("chunk", {}).get("chunk_index"),
                "excerpt": str(h.get("chunk", {}).get("text", ""))[:1200],
            }
            for h in hits
        ],
    }

    save_json(ANSWER_REPORT, report)

    report_path = REPORTS / f"document_answer_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, report)
    report["report_path"] = str(report_path)

    return report


def document_answer_status() -> dict[str, Any]:
    index = load_json(INDEX, [])
    chunks = load_json(CHUNKS, [])
    return {
        "tool": "Document Answer Engine V2",
        "timestamp": now_iso(),
        "documents": len(index) if isinstance(index, list) else 0,
        "chunks": len(chunks) if isinstance(chunks, list) else 0,
        "answer_report": str(ANSWER_REPORT),
    }


if __name__ == "__main__":
    print(json.dumps(document_answer_status(), indent=2, ensure_ascii=False))
