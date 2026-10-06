"""Το /chat κρατά το conversation_id και σέβεται το research mode."""

import pytest

pytest.importorskip("flask")


def test_chat_route_forwards_conversation_and_research_mode(monkeypatch):
    monkeypatch.setenv("NOUS_TOKEN", "testtoken123")
    import executor.router as router

    calls = []

    def fake_response(message, conversation_id=None, research_mode="auto"):
        calls.append((message, conversation_id, research_mode))
        return {"ok": True, "answer": "ok", "conversation_id": conversation_id or "new"}

    monkeypatch.setattr(router, "_chat_intent_route", lambda _msg: None)
    monkeypatch.setattr(router, "chatgpt_style_response", fake_response)

    client = router.app.test_client()
    response = client.post(
        "/chat",
        json={"message": "γεια", "conversation_id": "conv-1", "researchMode": "off"},
        headers={"Authorization": "Bearer testtoken123"},
    )

    assert response.status_code == 200
    assert response.get_json()["conversation_id"] == "conv-1"
    assert calls == [("γεια", "conv-1", "off")]


def test_research_off_skips_web(monkeypatch):
    import executor.chat_brain_v3 as brain

    for name in ("natural_chat_answer", "capability_answer", "identity_answer", "casual_answer"):
        monkeypatch.setattr(brain, name, lambda *_a, **_k: None)
    monkeypatch.setattr(brain, "should_skip_knowledge_and_web", lambda _m: True)
    monkeypatch.setattr(brain, "has_internet_intent", lambda _m: True)
    monkeypatch.setattr(brain, "has_deep_research_intent", lambda _m: True)

    def fail(*_a, **_k):
        raise AssertionError("web search must not run when research is off")

    monkeypatch.setattr(brain, "deep_research", fail)
    monkeypatch.setattr(brain, "answer_from_web", fail)
    monkeypatch.setattr(brain, "try_llm_answer", lambda *_a, **_k: "llm")
    monkeypatch.setattr(brain, "learn_from_chat_result", lambda *_a, **_k: None)
    monkeypatch.setattr(brain, "remember_turn", lambda *_a, **_k: None)
    monkeypatch.setattr(
        brain, "append_turn", lambda **kwargs: {"conversation_id": kwargs.get("conversation_id")}
    )
    import executor.agent_loop as agent_loop

    monkeypatch.setattr(agent_loop, "run_agent", lambda *_a, **_k: {"ok": False})

    result = brain.answer_chat("ψάξε στο internet για NOUS", "conv-9", research_mode="off")

    assert result["answer"] == "llm"
    assert result["conversation_id"] == "conv-9"
