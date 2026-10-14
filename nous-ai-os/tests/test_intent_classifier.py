"""Unit tests for natural-language intent classifier and chat integration."""

from __future__ import annotations


def test_health_and_status_rules():
    from executor.intent_classifier import classify_intent

    h = classify_intent("έλεγχος υγείας", use_llm=False)
    assert h["intent"] in ("health_check", "system_status")
    s = classify_intent("κατάσταση", use_llm=False)
    assert s["intent"] in ("system_status", "health_check")


def test_identity_and_capabilities():
    from executor.intent_classifier import classify_intent

    i = classify_intent("ποιος είσαι", use_llm=False)
    assert i["intent"] == "identity"
    c = classify_intent("τι μπορείς να κάνεις", use_llm=False)
    assert c["intent"] == "capabilities"


def test_list_tools_rule():
    from executor.intent_classifier import classify_intent

    c = classify_intent("τι εργαλεία έχεις", use_llm=False)
    assert c["intent"] == "list_tools"


def test_create_mission_slots():
    from executor.intent_classifier import classify_intent

    c = classify_intent("φτιάξε αποστολή βελτίωσε το UI", use_llm=False)
    assert c["intent"] == "create_mission"
    assert "UI" in c.get("slots", {}).get("goal", "")


def test_memory_recall_rule():
    from executor.intent_classifier import classify_intent

    c = classify_intent("θυμάσαι για το deploy", use_llm=False)
    assert c["intent"] == "memory_recall"


def test_handle_autonomous_toggle(monkeypatch):
    from executor import mode as mode_mod
    from executor.intent_chat_integration import _handle_classified_intent

    mode_mod.enable()
    out = _handle_classified_intent(
        {"intent": "autonomous_status", "confidence": 0.95, "slots": {}},
        "αυτόνομη κατάσταση",
    )
    assert out and out.get("ok") is True

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


def test_privileged_repair_requests_approval():
    from executor.intent_classifier import classify_intent

    c = classify_intent("επισκευή συστήματος", use_llm=False)
    assert c["intent"] == "request_privileged_tool"
    assert c["slots"].get("action") == "repair_system"


def test_approve_and_run_rule():
    from executor.intent_classifier import classify_intent

    c = classify_intent("ενέκρινε και εκτέλεσε 12", use_llm=False)
    assert c["intent"] == "approve_and_run"
    assert c["slots"].get("approval_id") == "12"


def test_list_approvals_rule():
    from executor.intent_classifier import classify_intent

    c = classify_intent("εκκρεμείς εγκρίσεις", use_llm=False)
    assert c["intent"] == "list_approvals"


def test_nlp_parser_uses_intent():
    from executor.nlp_parser import parse_natural_command

    out = parse_natural_command("κατάσταση")
    assert "status" in out.lower() or out == "/status"


def test_format_tool_error():
    from executor.capability_awareness import format_tool_error

    msg = format_tool_error("git_status", code="test")
    assert "git_status" in msg
    assert "test" in msg


def test_session_context_roundtrip(tmp_path, monkeypatch):
    from executor import session_context as sc

    monkeypatch.setattr(sc, "_PATH", tmp_path / "ctx.json")
    sc.remember_classification({"intent": "capabilities", "confidence": 0.9, "slots": {}}, "τι μπορείς")
    last = sc.get_last()
    assert last and last.get("intent") == "capabilities"
