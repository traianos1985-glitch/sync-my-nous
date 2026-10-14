"""Unit tests for natural-language intent classification and handlers (rules path, no LLM)."""
from __future__ import annotations


def test_classify_status_and_health_rules():
    from executor.intent_classifier import classify_intent

    r = classify_intent("κατάσταση", use_llm=False)
    assert r["intent"] in ("system_status", "health_check")
    assert r["confidence"] >= 0.72
    assert r["needs_clarification"] is False

    r2 = classify_intent("έλεγχος υγείας", use_llm=False)
    assert r2["intent"] == "health_check"


def test_classify_create_mission_and_goal():
    from executor.intent_classifier import classify_intent

    r = classify_intent("φτιάξε αποστολή βελτίωσε το UI", use_llm=False)
    assert r["intent"] == "create_mission"
    assert "UI" in r["slots"].get("goal", "") or "βελτίωσε" in r["slots"].get("goal", "")

    r2 = classify_intent("δημιούργησε στόχο: να μάθω Rust", use_llm=False)
    assert r2["intent"] == "create_goal"
    assert "Rust" in r2["slots"].get("title", "")


def test_classify_memory_and_search():
    from executor.intent_classifier import classify_intent

    r = classify_intent("θυμάσαι για το deploy", use_llm=False)
    assert r["intent"] == "memory_recall"

    r2 = classify_intent("ψάξε για Python asyncio", use_llm=False)
    assert r2["intent"] == "search_web"
    assert "Python" in r2["slots"].get("query", "")


def test_classify_read_url_evolve_autonomous():
    from executor.intent_classifier import classify_intent

    r = classify_intent("διάβασε https://example.com/page", use_llm=False)
    assert r["intent"] == "read_url"
    assert r["slots"]["url"].startswith("https://example.com")

    r2 = classify_intent("εξέλιξη συστήματος", use_llm=False)
    assert r2["intent"] == "evolve"

    r3 = classify_intent("ξεκίνα την αυτόνομη λειτουργία", use_llm=False)
    assert r3["intent"] == "autonomous_start"

    r4 = classify_intent("σταμάτα την αυτόνομη", use_llm=False)
    assert r4["intent"] == "autonomous_stop"

    r5 = classify_intent("κατάσταση αυτόνομης λειτουργίας", use_llm=False)
    assert r5["intent"] in ("autonomous_status", "system_status")


def test_empty_message_needs_clarification():
    from executor.intent_classifier import classify_intent

    r = classify_intent("", use_llm=False)
    assert r["needs_clarification"] is True


def test_handle_autonomous_mode():
    from executor import mode as mode_mod
    from executor.intent_chat_integration import _handle_classified_intent

    mode_mod.MODE["autonomous"] = False
    out = _handle_classified_intent(
        {"intent": "autonomous_start", "confidence": 0.95, "slots": {}},
        "ξεκίνα την αυτόνομη",
    )
    assert out and out.get("ok") is True
    assert mode_mod.status().get("autonomous") is True

    out2 = _handle_classified_intent(
        {"intent": "autonomous_stop", "confidence": 0.95, "slots": {}},
        "σταμάτα",
    )
    assert out2 and out2.get("ok") is True
    assert mode_mod.status().get("autonomous") is False


def test_handle_create_goal(monkeypatch):
    from executor import goal_system
    from executor.intent_chat_integration import _handle_classified_intent

    def fake_create(title, description="", priority=3):
        return {"id": 42, "title": title}

    monkeypatch.setattr(goal_system, "create_goal", fake_create)
    out = _handle_classified_intent(
        {"intent": "create_goal", "confidence": 0.95, "slots": {"title": "να μάθω Rust"}},
        "δημιούργησε στόχο να μάθω Rust",
    )
    assert out and out.get("executed") is True
    assert "Rust" in out.get("answer", "")


def test_try_intent_route_rules_only(monkeypatch):
    from executor import intent_chat_integration as ici
    from executor import intent_classifier as ic

    def fake_classify(message, use_llm=True):
        return ic.classify_intent(message, use_llm=False)

    monkeypatch.setattr(ici, "classify_intent", fake_classify)
    routed = ici.try_intent_route("ποιος είσαι")
    assert routed is not None
    assert routed.get("intent") == "identity"
