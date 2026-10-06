"""Render: web search fallback, honest reality summary, data-file restore."""

import requests


def test_web_search_falls_back_when_duckduckgo_times_out(monkeypatch):
    import executor.internet_search_engine as engine
    import executor.research_agent as agent

    def timeout(*_a, **_k):
        raise requests.ConnectTimeout("blocked")

    monkeypatch.setattr(agent, "_ddg_search", timeout)
    monkeypatch.setattr(
        engine,
        "search_web",
        lambda q: {"results": [{"title": "Flask", "url": "https://en.wikipedia.org/wiki/Flask", "snippet": "web"}]},
    )

    result = agent.web_search("Python Flask")
    assert result["results"][0]["url"] == "https://en.wikipedia.org/wiki/Flask"


def test_reality_summary_reflects_failed_checks(monkeypatch):
    import executor.reality_gate as gate

    monkeypatch.setattr(gate, "check_internet", lambda: {"real": False})
    monkeypatch.setattr(gate, "check_browser_read", lambda: {"real": True})
    monkeypatch.setattr(gate, "check_android", lambda: {"real_intents": False})
    monkeypatch.setattr(gate, "check_git", lambda: {"real": False})
    monkeypatch.setattr(gate, "check_code", lambda: {"real": True})
    monkeypatch.setattr(gate, "check_app_factory", lambda: {"real": True})

    summary = gate.reality_status()["summary"]
    assert summary["real_now"] == ["browser_read", "code_compile", "app_factory"]
    assert summary["unavailable_now"] == ["internet_search", "android_intents", "git_status"]


def test_restore_missing_data_files(tmp_path, monkeypatch):
    import json

    import executor.nous_drive as drive

    monkeypatch.chdir(tmp_path)
    backup = tmp_path / "data" / "backups" / "nous_data_1"
    backup.mkdir(parents=True)
    (backup / "brain_state.json").write_text(json.dumps({"name": "NOUS"}), encoding="utf-8")

    restored = drive.restore_missing_data_files()

    assert set(restored) == set(drive.CRITICAL_DATA_FILES)
    assert json.loads((tmp_path / "data" / "brain_state.json").read_text()) == {"name": "NOUS"}
    assert json.loads((tmp_path / "data" / "api_tokens.json").read_text()) == []
    assert drive.restore_missing_data_files() == {}
