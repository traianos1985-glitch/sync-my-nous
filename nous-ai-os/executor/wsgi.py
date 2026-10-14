"""WSGI entrypoint: prefer unified intent classifier before router.chat().

Render/Docker use this module (`executor.wsgi:app`) so search and other NL
intents are not intercepted by the legacy browser_operator path first.
"""

from __future__ import annotations

from flask import jsonify, request

from executor.router import app

_orig_chat = app.view_functions.get("chat")

if _orig_chat is not None:

    def chat_intent_first():  # type: ignore[no-redef]
        try:
            from executor.security import check_token

            if not check_token(request):
                return jsonify({"error": "unauthorized"}), 401
            data = request.get_json(silent=True) or {}
            msg = (
                data.get("message")
                or data.get("prompt")
                or data.get("text")
                or data.get("command")
                or ""
            )
            from executor.intent_chat_integration import try_intent_route

            routed = try_intent_route(str(msg))
            if routed is not None:
                return jsonify(routed)
        except Exception:
            pass
        return _orig_chat()

    app.view_functions["chat"] = chat_intent_first

__all__ = ["app"]
