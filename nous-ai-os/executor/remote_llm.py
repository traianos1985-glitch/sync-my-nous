import os

import requests

from executor.local_llm_adapter import ask_ollama

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.5-flash:generateContent"
)
TIMEOUT = 60

SYSTEM_PROMPT = (
    "Είσαι ο ΝΟΥΣ, ένας έξυπνος AI βοηθός στα ελληνικά. "
    "Απάντα πάντα σε φυσικά, σωστά ελληνικά. "
    "Μην απαντάς με JSON εκτός αν σου ζητηθεί ρητά. "
    "Δώσε σαφή και ολοκληρωμένη απάντηση — μην σταματάς πριν ολοκληρώσεις."
)


def _api_key() -> str:
    """Accept the supported Gemini key names used by local and cloud deployments."""
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY", "GCP_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def _call_gemini(contents: list, system: str, max_tokens: int = 4096) -> dict:
    key = _api_key()
    if not key:
        return {"success": False, "error": "no_gemini_api_key", "provider": "gemini"}

    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": max_tokens},
    }
    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": key},
            json=payload,
            timeout=TIMEOUT,
        )
        data = response.json()
        if not response.ok:
            error = data.get("error", {})
            message = error.get("message", "request_failed") if isinstance(error, dict) else "request_failed"
            return {
                "success": False,
                "error": f"gemini_http_{response.status_code}:{message}",
                "provider": "gemini",
            }
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            return {"success": False, "error": "gemini_empty_response", "provider": "gemini"}
        return {
            "success": True,
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "response": text,
        }
    except requests.RequestException:
        # Do not return exception text: request URLs may contain sensitive credentials.
        return {"success": False, "error": "gemini_request_failed", "provider": "gemini"}
    except (ValueError, KeyError, IndexError, TypeError):
        return {"success": False, "error": "gemini_invalid_response", "provider": "gemini"}


def _local_purpose(prompt: str) -> str:
    coding_terms = (
        "code", "coding", "python", "javascript", "typescript", "bug", "debug",
        "function", "api", "program", "κώδικ", "πρόγραμμα", "σφάλμα", "τεστ",
    )
    return "coding" if any(term in str(prompt).lower() for term in coding_terms) else "general"


def _contents_from_turns(turns: list[dict]) -> list[dict]:
    contents = []
    for turn in turns:
        role = turn.get("role")
        if role == "system":
            continue
        if role not in ("user", "assistant", "model"):
            continue
        contents.append(
            {
                "role": "model" if role in ("assistant", "model") else "user",
                "parts": [{"text": str(turn.get("content", ""))}],
            }
        )
    return contents


def _post(messages: list, max_tokens: int = 4096) -> dict:
    """Compatibility wrapper for callers using chat-completions messages."""
    system = SYSTEM_PROMPT
    turns = []
    for message in messages:
        if message.get("role") == "system":
            system = str(message.get("content", SYSTEM_PROMPT))
        else:
            turns.append(message)
    return _call_gemini(_contents_from_turns(turns), system, max_tokens)


def _ask_gemini(prompt: str) -> dict:
    return _call_gemini(
        [{"role": "user", "parts": [{"text": prompt}]}],
        SYSTEM_PROMPT,
    )


def check_gemini(prompt: str = "Απάντησε ακριβώς με GEMINI_OK") -> dict:
    """Call Gemini directly without falling back to another provider."""
    return _ask_gemini(prompt)


def ask_remote_llm(prompt: str) -> dict:
    """Single-turn Gemini call, with the existing optional local Ollama fallback."""
    gemini = _ask_gemini(prompt)
    if gemini.get("success"):
        return gemini

    local = ask_ollama(prompt, purpose=_local_purpose(prompt))
    if local.get("ok"):
        return {
            "success": True,
            "provider": "ollama_fallback",
            "model": local["model"],
            "response": local["response"],
        }
    return gemini


def ask_with_turns(turns: list[dict], system: str | None = None) -> dict:
    """Multi-turn Gemini chat using {role, content} turns."""
    return _call_gemini(
        _contents_from_turns(turns),
        system or SYSTEM_PROMPT,
    )


def ask_with_image(
    prompt: str,
    image_b64: str,
    mime: str = "image/jpeg",
    system: str | None = None,
) -> dict:
    """Send text and an inline image to Gemini's vision-capable model."""
    return _call_gemini(
        [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime, "data": image_b64}},
                ],
            }
        ],
        system or SYSTEM_PROMPT,
        max_tokens=2400,
    )
