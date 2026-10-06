import os
import os
from unittest.mock import patch

import pytest

from executor import remote_llm


class FakeResponse:
    ok = True
    status_code = 200

    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": "GEMINI_OK"}]}}]}


def test_simple_chat_uses_gemini_and_prefers_current_key_name():
    with (
        patch.dict(os.environ, {"GEMINI_API_KEY": "current-key", "GCP_API_KEY": "old-key"}),
        patch.object(remote_llm.requests, "post", return_value=FakeResponse()) as post,
        patch.object(remote_llm, "ask_ollama") as ollama,
    ):
        result = remote_llm.ask_remote_llm("hello")

    assert result["success"] is True
    assert result["provider"] == "gemini"
    assert result["response"] == "GEMINI_OK"
    assert post.call_args.kwargs["params"] == {"key": "current-key"}
    assert post.call_args.kwargs["json"]["contents"][0]["parts"][0]["text"] == "hello"
    ollama.assert_not_called()


def test_configured_fallback_model_is_used_after_quota_exhaustion():
    class QuotaResponse:
        ok = False
        status_code = 429

        def json(self):
            return {"error": {"message": "quota exceeded"}}

    with (
        patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "current-key",
                "GEMINI_MODEL": "gemini-primary",
                "GEMINI_FALLBACK_MODELS": "gemini-fallback",
            },
            clear=True,
        ),
        patch.object(remote_llm.requests, "post", side_effect=[QuotaResponse(), FakeResponse()]) as post,
        patch.object(remote_llm, "ask_ollama") as ollama,
    ):
        result = remote_llm.ask_remote_llm("hello")

    assert result["success"] is True
    assert result["model"] == "gemini-fallback"
    assert post.call_count == 2
    assert post.call_args_list[0].args[0].endswith("/gemini-primary:generateContent")
    assert post.call_args_list[1].args[0].endswith("/gemini-fallback:generateContent")
    ollama.assert_not_called()


def test_all_configured_models_unavailable_returns_failure_without_fake_answer():
    class QuotaResponse:
        ok = False
        status_code = 429

        def json(self):
            return {"error": {"message": "quota exceeded"}}

    with (
        patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "current-key",
                "GEMINI_MODEL": "gemini-primary",
                "GEMINI_FALLBACK_MODELS": "gemini-fallback",
            },
            clear=True,
        ),
        patch.object(remote_llm.requests, "post", side_effect=[QuotaResponse(), QuotaResponse()]),
        patch.object(remote_llm, "ask_ollama", return_value={"ok": False}),
    ):
        result = remote_llm.ask_remote_llm("hello")

    assert result["success"] is False
    assert result["model"] == "gemini-fallback"
    assert "hello" not in result.get("response", "")


def test_multiturn_chat_sends_assistant_history_to_gemini():
    with (
        patch.dict(os.environ, {"GEMINI_API_KEY": "current-key"}),
        patch.object(remote_llm.requests, "post", return_value=FakeResponse()) as post,
    ):
        result = remote_llm.ask_with_turns(
            [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}],
            system="Test system",
        )

    contents = post.call_args.kwargs["json"]["contents"]
    assert result["provider"] == "gemini"
    assert post.call_args.kwargs["json"]["systemInstruction"]["parts"][0]["text"] == "Test system"
    assert contents[1] == {"role": "model", "parts": [{"text": "Hi"}]}


def test_image_analysis_sends_inline_image_to_gemini():
    with (
        patch.dict(os.environ, {"GEMINI_API_KEY": "current-key"}),
        patch.object(remote_llm.requests, "post", return_value=FakeResponse()) as post,
    ):
        result = remote_llm.ask_with_image("Describe this", "aGVsbG8=", "image/png")

    parts = post.call_args.kwargs["json"]["contents"][0]["parts"]
    assert result["provider"] == "gemini"
    assert parts[1] == {"inlineData": {"mimeType": "image/png", "data": "aGVsbG8="}}


def test_gemini_errors_never_return_key_or_fall_back_to_openrouter():
    with (
        patch.dict(os.environ, {"GEMINI_API_KEY": "secret-key"}, clear=True),
        patch.object(remote_llm.requests, "post", side_effect=remote_llm.requests.Timeout()),
        patch.object(remote_llm, "ask_ollama", return_value={"ok": False}),
    ):
        result = remote_llm.ask_remote_llm("hello")

    assert result["success"] is False
    assert result["provider"] == "gemini"
    assert "secret-key" not in str(result)
    assert "openrouter" not in str(result).lower()


@pytest.mark.parametrize("path", ["/api/gemini-check", "/gemini-check"])
def test_dashboard_gemini_check_route_uses_authenticated_gemini(path, monkeypatch):
    from executor import router

    monkeypatch.setenv("NOUS_TOKEN", "route-test-token")
    monkeypatch.setattr(
        router,
        "check_gemini",
        lambda prompt: {
            "success": True,
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "response": "GEMINI_OK",
        },
    )
    response = router.app.test_client().post(
        path,
        json={"message": "Απάντησε ακριβώς με GEMINI_OK"},
        headers={"Authorization": "Bearer route-test-token"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "ok": True,
        "source": "gemini",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "response": "GEMINI_OK",
    }
