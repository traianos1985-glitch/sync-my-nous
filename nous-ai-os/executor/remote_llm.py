import requests
import os

from executor.local_llm_adapter import ask_ollama

API_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

MODELS = [
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "meta-llama/llama-3.3-8b-instruct:free",
    "google/gemma-3-12b-it:free",
    "openrouter/auto",
]

VISION_MODELS = [
    "google/gemma-3-12b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "openrouter/auto",
]

TIMEOUT = 60

SYSTEM_PROMPT = (
    "Είσαι ο ΝΟΥΣ, ένας έξυπνος AI βοηθός στα ελληνικά. "
    "Απάντα πάντα σε φυσικά, σωστά ελληνικά. "
    "Μην απαντάς με JSON εκτός αν σου ζητηθεί ρητά. "
    "Δώσε σαφή και ολοκληρωμένη απάντηση — μην σταματάς πριν ολοκληρώσεις."
)


def _post(messages: list, max_tokens: int = 4096) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return {"success": False, "error": "no_api_key"}

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nous.local",
        "X-Title": "NOUS-AI-OS",
    }

    last_error = None
    for model in MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
            data = r.json()
            if "choices" in data and data["choices"]:
                text = data["choices"][0]["message"]["content"].strip()
                if text:
                    return {"success": True, "model": model, "response": text}
            last_error = str(data)
        except Exception as e:
            last_error = str(e)
            continue

    return {"success": False, "error": last_error or "no_response"}


def _local_purpose(prompt: str) -> str:
    coding_terms = (
        "code", "coding", "python", "javascript", "typescript", "bug", "debug",
        "function", "api", "program", "κώδικ", "πρόγραμμα", "σφάλμα", "τεστ",
    )
    return "coding" if any(term in str(prompt).lower() for term in coding_terms) else "general"


def _ask_gemini(prompt: str) -> dict:
    key = os.environ.get("GCP_API_KEY", "")
    if not key:
        return {"success": False, "error": "no_gcp_api_key"}
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096},
    }
    try:
        response = requests.post(f"{GEMINI_URL}?key={key}", json=payload, timeout=TIMEOUT)
        data = response.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts).strip()
        if response.ok and text:
            return {"success": True, "provider": "gemini", "model": "gemini-2.5-flash", "response": text}
        return {"success": False, "error": str(data)}
    except Exception as error:
        return {"success": False, "error": str(error)}


def ask_remote_llm(prompt: str) -> dict:
    """Single-turn: Gemini API, OpenRouter, then local Ollama."""
    gemini = _ask_gemini(prompt)
    if gemini.get("success"):
        return gemini

    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        local = ask_ollama(prompt, purpose=_local_purpose(prompt))
        if local.get("ok"):
            return {"success": True, "provider": "ollama", "model": local["model"], "response": local["response"]}
        return {"success": False, "error": gemini.get("error", local.get("error", local.get("reason", "local_llm_unavailable"))), "provider": "ollama"}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    res = _post(messages)
    if res.get("success"):
        return res
    # Automatic hybrid fallback to Ollama if remote call failed
    local = ask_ollama(prompt, purpose=_local_purpose(prompt))
    if local.get("ok"):
        return {"success": True, "provider": "ollama_fallback", "model": local["model"], "response": local["response"]}
    return res


def ask_with_turns(turns: list[dict], system: str | None = None) -> dict:
    """Multi-turn: pass a list of {role, content} dicts (user/assistant alternating).
    System prompt is prepended automatically."""
    messages = [{"role": "system", "content": system or SYSTEM_PROMPT}]
    messages.extend(turns)
    return _post(messages)


def ask_with_image(prompt: str, image_b64: str, mime: str = "image/jpeg",
                   system: str | None = None) -> dict:
    """Vision: send an image (base64) + text prompt to a vision-capable model."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return {"success": False, "error": "no_api_key"}

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nous.local",
        "X-Title": "NOUS-AI-OS",
    }
    sys_msg = system or SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": sys_msg},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
            ],
        },
    ]

    last_error = None
    for model in VISION_MODELS:
        payload = {"model": model, "messages": messages,
                   "max_tokens": 2400, "temperature": 0.3}
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            data = r.json()
            if "choices" in data and data["choices"]:
                text = data["choices"][0]["message"]["content"].strip()
                if text:
                    return {"success": True, "model": model, "response": text}
            last_error = str(data)
        except Exception as e:
            last_error = str(e)
            continue

    return {"success": False, "error": last_error or "no_response"}
