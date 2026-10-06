import os

import requests

from executor.local_llm_adapter import ask_ollama

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_FALLBACK_MODELS = "gemini-2.5-flash-lite"
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


def configured_models() -> list[str]:
    primary = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    fallbacks = os.environ.get(
        "GEMINI_FALLBACK_MODELS", DEFAULT_GEMINI_FALLBACK_MODELS
    ).split(",")
    return list(dict.fromkeys([primary, *(model.strip() for model in fallbacks if model.strip())]))


def _call_gemini(
    contents: list,
    system: str,
    max_tokens: int = 4096,
    model: str | None = None,
) -> dict:
    key = _api_key()
    if not key:
        return {"success": False, "error": "no_gemini_api_key", "provider": "gemini"}

    selected_model = model or configured_models()[0]
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": max_tokens},
    }
    try:
        response = requests.post(
            f"{GEMINI_API_BASE}/{selected_model}:generateContent",
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
                "model": selected_model,
            }
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            return {"success": False, "error": "gemini_empty_response", "provider": "gemini", "model": selected_model}
        return {
            "success": True,
            "provider": "gemini",
            "model": selected_model,
            "response": text,
        }
    except requests.RequestException:
        return {"success": False, "error": "gemini_request_failed", "provider": "gemini", "model": selected_model}
    except (ValueError, KeyError, IndexError, TypeError):
        return {"success": False, "error": "gemini_invalid_response", "provider": "gemini", "model": selected_model}


def _can_fallback(result: dict) -> bool:
    error = str(result.get("error", "")).lower()
    return (
        "quota" in error
        or "resource_exhausted" in error
        or "gemini_http_429" in error
        or any(f"gemini_http_{status}" in error for status in (403, 404, 408, 500, 502, 503, 504))
    )


def _call_gemini_with_fallback(contents: list, system: str, max_tokens: int = 4096) -> dict:
    models = configured_models()
    result = _call_gemini(contents, system, max_tokens, model=models[0])
    for model in models[1:]:
        if result.get("success") or not _can_fallback(result):
            break
        result = _call_gemini(contents, system, max_tokens, model=model)
    return result


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
    gemini = _call_gemini_with_fallback(
        [{"role": "user", "parts": [{"text": prompt}]}], SYSTEM_PROMPT
    )
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
    system_prompt = system or SYSTEM_PROMPT
    result = _call_gemini_with_fallback(_contents_from_turns(turns), system_prompt)
    if result.get("success"):
        return result

    prompt = "\n\n".join(
        f"{turn.get('role', 'user')}: {turn.get('content', '')}"
        for turn in turns
        if turn.get("role") != "system"
    )
    local = ask_ollama(f"{system_prompt}\n\n{prompt}", purpose=_local_purpose(prompt))
    if local.get("ok"):
        return {
            "success": True,
            "provider": "ollama_fallback",
            "model": local["model"],
            "response": local["response"],
        }
    return result


def ask_with_image(
    prompt: str,
    image_b64: str,
    mime: str = "image/jpeg",
    system: str | None = None,
) -> dict:
    """Send text and an inline image to Gemini's vision-capable model."""
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": prompt},
                {"inlineData": {"mimeType": mime, "data": image_b64}},
            ],
        }
    ]
    return _call_gemini_with_fallback(contents, system or SYSTEM_PROMPT, max_tokens=2400)
