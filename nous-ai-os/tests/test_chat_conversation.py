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


def test_app_builder_plan_requires_authentication(monkeypatch):
    import executor.router as router

    monkeypatch.setenv("NOUS_TOKEN", "testtoken123")
    monkeypatch.setattr(router, "plan_app", lambda *_a: pytest.fail("must not create a plan"))

    response = router.app.test_client().post(
        "/remote/app-builder/plan", json={"description": "Build a tool"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_app_builder_file_write_requires_authenticated_approval(monkeypatch):
    import executor.router as router

    monkeypatch.setenv("NOUS_TOKEN", "testtoken123")
    monkeypatch.setattr(router, "approve_and_write", lambda *_a: pytest.fail("must not write files"))

    response = router.app.test_client().post(
        "/remote/app-builder/approve", json={"plan_id": "plan-1"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_chat_rejects_unauthenticated_actions_before_routing(monkeypatch):
    import executor.router as router

    monkeypatch.setenv("NOUS_TOKEN", "testtoken123")
    monkeypatch.setattr(router, "_chat_intent_route", lambda _msg: pytest.fail("route must not run"))

    response = router.app.test_client().post(
        "/chat", json={"message": "Δημιούργησε στόχο: να μάθω Rust"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


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


def test_calculator_accepts_question_mark_and_semicolon():
    import executor.chat_brain_v3 as brain

    assert brain.calculator_answer("Πόσο κάνει 37*91;") == "Το αποτέλεσμα είναι: 3367"
    assert brain.calculator_answer("Πόσο κάνει 37*91?") == "Το αποτέλεσμα είναι: 3367"


def test_chat_reports_unavailable_llm_without_echoing_prompt(monkeypatch):
    import executor.chat_brain_v3 as brain
    import executor.agent_loop as agent_loop

    for name in (
        "natural_chat_answer", "capability_answer", "identity_answer", "casual_answer",
        "answer_from_knowledge_memory", "answer_from_conversations",
        "cross_conversation_context", "deep_research", "answer_from_web",
        "summarize_search_results", "memory_question_answer", "user_statement_answer",
    ):
        monkeypatch.setattr(brain, name, lambda *_a, **_k: None)
    for name in (
        "has_document_intent", "has_conversation_search_intent", "has_cross_memory_intent",
        "has_deep_research_intent", "has_internet_intent", "has_calc_intent",
    ):
        monkeypatch.setattr(brain, name, lambda *_a, **_k: False)
    monkeypatch.setattr(brain, "should_skip_knowledge_and_web", lambda _message: True)
    monkeypatch.setattr(brain, "extract_urls", lambda _message: [])
    monkeypatch.setattr(agent_loop, "run_agent", lambda *_a, **_k: {"ok": False, "mode": "llm_unavailable"})
    monkeypatch.setattr(brain, "try_llm_answer", lambda *_a, **_k: pytest.fail("do not retry after provider failure"))

    result = brain.answer_chat("Εξήγησε την κβαντική φυσική")

    assert result["ok"] is False
    assert result["mode"] == "degraded"
    assert result["error"] == "llm_unavailable"
    assert "Δεν είναι διαθέσιμο" in result["answer"]
    assert "Εξήγησε την κβαντική φυσική" not in result["answer"]


def test_failed_provider_response_is_not_used_as_chat_answer(monkeypatch):
    import executor.chat_brain_v3 as brain
    from executor import remote_llm

    monkeypatch.setattr(brain, "coding_context", lambda _message: "")
    monkeypatch.setattr(brain, "engineering_memory_context", lambda _message: "")
    monkeypatch.setattr(brain, "document_context_for_llm", lambda _message: "")
    monkeypatch.setattr(brain, "build_llm_turns", lambda *_a, **_k: [])
    monkeypatch.setattr(
        remote_llm,
        "ask_with_turns",
        lambda *_a, **_k: {"success": False, "response": "echo of user prompt"},
    )

    assert brain.try_llm_answer("hello") is None


def test_goal_creation_reports_only_persisted_result(monkeypatch):
    import executor.goal_system as goals
    from executor.natural_chat_orchestrator import natural_chat_answer

    monkeypatch.setattr(goals, "create_goal", lambda title: {"id": 23, "title": title})
    created = natural_chat_answer("Δημιούργησε στόχο: να μάθω Rust")
    assert created["ok"] is True
    assert created["executed"] is True
    assert created["goal_id"] == "23"
    assert "Rust" in created["answer"]

    monkeypatch.setattr(goals, "create_goal", lambda _title: {})
    failed = natural_chat_answer("Δημιούργησε στόχο: να μάθω Rust")
    assert failed["ok"] is False
    assert failed["executed"] is False


def test_chat_does_not_route_text_improvement_or_tool_word_as_action(monkeypatch):
    from executor import router

    monkeypatch.setattr(router, "propose_upgrade_plan", lambda: pytest.fail("should not propose upgrade"))
    assert router._chat_intent_route("βελτίωσε το κείμενό σου") is None
    assert router._chat_intent_route("κάνε αυτό εργαλείο") is None


def test_upgrade_intent_creates_pending_plan_without_approval(monkeypatch):
    from executor import router

    monkeypatch.setattr(
        router,
        "propose_upgrade_plan",
        lambda: {"ok": True, "plan": {"id": 12, "status": "pending"}},
    )
    monkeypatch.setattr(router, "approve_upgrade_plan", lambda *_a: pytest.fail("must wait for approval"))

    result = router._chat_intent_route("βελτίωσε τον NOUS")

    assert result["ok"] is True
    assert result["executed"] is False
    assert "αναμονή" in result["answer"]
    assert result["plan_id"] == "12"


def test_system_status_combines_live_mission_and_operator_approvals(monkeypatch):
    import executor.goal_system as goals
    import executor.mission_system as missions
    import executor.operator_approval as operator_approval
    from executor.natural_chat_orchestrator import _system_status_answer

    monkeypatch.setattr(goals, "goal_status", lambda: {"total": 2, "active": 1})
    monkeypatch.setattr(
        missions,
        "mission_status",
        lambda: {"total": 3, "active": 1, "done": 1, "blocked": 1},
    )
    monkeypatch.setattr(missions, "pending_approvals", lambda: {"count": 2})
    monkeypatch.setattr(operator_approval, "list_approvals", lambda status=None: [{"status": "pending"}])

    answer = _system_status_answer()

    assert "Αποστολές: 3 συνολικά" in answer
    assert "Στόχοι: 2 συνολικά" in answer
    assert "Εκκρεμείς εγκρίσεις: 3" in answer


def test_backup_chat_confirms_only_a_created_archive(monkeypatch):
    import executor.cloud_brain_backup as backup_module
    from executor.natural_chat_orchestrator import natural_chat_answer

    monkeypatch.setattr(
        backup_module,
        "create_brain_backup",
        lambda: {"ok": True, "backup": "data/brain_backups/test.zip"},
    )
    result = natural_chat_answer("Κάνε backup")
    assert result["ok"] is True
    assert result["executed"] is True
    assert result["backup"] == "data/brain_backups/test.zip"

    monkeypatch.setattr(backup_module, "create_brain_backup", lambda: {"ok": False})
    failed = natural_chat_answer("Κάνε backup")
    assert failed["ok"] is False
    assert failed["executed"] is False


def test_requested_weather_location_uses_real_result(monkeypatch):
    import executor.weather_engine as weather_engine
    from executor.natural_chat_orchestrator import natural_chat_answer

    monkeypatch.setattr(
        weather_engine,
        "get_weather",
        lambda location=None: {
            "ok": True,
            "location": location,
            "current": {"description": "Αίθριος", "temp": 24, "humidity": 50, "wind_kmh": 8},
        },
    )
    result = natural_chat_answer("Καιρός στην Αθήνα")

    assert result["ok"] is True
    assert result["executed"] is True
    assert result["location"] == "αθήνα"
    assert "αθήνα" in result["answer"]


def test_weather_cache_is_separated_by_requested_city(tmp_path, monkeypatch):
    import executor.weather_engine as weather_engine

    monkeypatch.setattr(weather_engine, "CACHE_FILE", tmp_path / "weather.json")
    calls = []

    class FakeResponse:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            return None

        def json(self):
            return self.data

    def fake_get(url, params, timeout):
        calls.append((url, params))
        if "geocoding" in url:
            return FakeResponse({"results": [{"name": params["name"], "latitude": len(calls), "longitude": 2, "country": "Ελλάδα"}]})
        return FakeResponse({"current": {"temperature_2m": 20, "relative_humidity_2m": 40, "wind_speed_10m": 5, "weather_code": 0, "precipitation": 0}})

    monkeypatch.setattr(weather_engine.requests, "get", fake_get)
    athens = weather_engine.get_weather(location="Αθήνα")
    patras = weather_engine.get_weather(location="Πάτρα")
    weather_engine.get_weather(location="Αθήνα")

    assert athens["ok"] is True
    assert patras["ok"] is True
    assert athens["location"].startswith("Αθήνα")
    assert patras["location"].startswith("Πάτρα")
    assert len(calls) == 4
