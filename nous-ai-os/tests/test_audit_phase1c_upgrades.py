"""Audit Phase 1c: N-03, N-05, N-06, N-07, F-04 and N-01 upgrades."""
import importlib
import json
import sys
import threading
import time
from pathlib import Path

import pytest


def _wait_for(predicate, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


# ----------------------------------------------------------------- N-03 autonomy loop

@pytest.fixture
def autonomy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from executor import autonomy_service

    service = importlib.reload(autonomy_service)
    calls = []
    monkeypatch.setattr(service, "run_once", lambda: calls.append("run_once") or {"ran": True})
    monkeypatch.setattr(service, "auto_learning_cycle", lambda: calls.append("learning") or {"ok": True})
    monkeypatch.setattr(service, "master_cycle", lambda real_research=False: calls.append("master") or {"ok": True})
    monkeypatch.setattr(service, "battery_guard", lambda: {"ok": True})
    service._test_calls = calls
    yield service
    service.stop_loop("test_teardown", timeout=5)


def test_status_reports_loop_not_running_when_only_enabled(autonomy):
    autonomy.enable(30)
    status = autonomy.status()
    assert status["enabled"] is True
    assert status["loop_running"] is False


def test_start_loop_runs_real_cycles_and_updates_heartbeat(autonomy):
    autonomy.enable(30)
    result = autonomy.start_loop(initial_delay=0)
    assert result["ok"] is True and result["loop_running"] is True
    assert _wait_for(lambda: autonomy.status()["cycles"] >= 1)
    status = autonomy.status()
    assert status["loop_running"] is True
    assert status["loop_mode"] == "managed_thread"
    assert status["last_heartbeat"] is not None
    assert autonomy._test_calls[:3] == ["run_once", "learning", "master"]
    assert autonomy.start_loop(initial_delay=0)["already_running"] is True


def test_loop_repeats_on_interval(autonomy, monkeypatch):
    monkeypatch.setattr(autonomy, "MIN_INTERVAL", 1)
    autonomy.enable(1)
    autonomy.start_loop(initial_delay=0)
    assert _wait_for(lambda: autonomy.status()["cycles"] >= 2, timeout=6)


def test_stop_loop_and_disable_stop_the_thread(autonomy):
    autonomy.enable(30)
    autonomy.start_loop(initial_delay=0)
    assert _wait_for(autonomy.loop_running)
    autonomy.disable()
    assert _wait_for(lambda: not autonomy.loop_running())
    assert autonomy.status()["loop_running"] is False


def test_emergency_stop_halts_loop_and_blocks_restart(autonomy):
    autonomy.enable(30)
    autonomy.start_loop(initial_delay=0)
    autonomy.emergency_stop("test")
    assert _wait_for(lambda: not autonomy.loop_running())
    refused = autonomy.start_loop(initial_delay=0)
    assert refused["ok"] is False and refused["error"] == "emergency_stop_active"


def test_start_loop_refused_when_disabled(autonomy):
    result = autonomy.start_loop(initial_delay=0)
    assert result["ok"] is False and result["error"] == "autonomy_disabled"
    assert autonomy.loop_running() is False


def test_failed_cycle_keeps_loop_alive_and_records_error(autonomy, monkeypatch):
    def boom():
        raise RuntimeError("cycle exploded")

    monkeypatch.setattr(autonomy, "run_once", boom)
    autonomy.enable(30)
    autonomy.start_loop(initial_delay=0)
    assert _wait_for(lambda: autonomy.status().get("last_error") == "RuntimeError")
    assert _wait_for(lambda: autonomy.status()["loop"]["last_outcome"] == "error")
    assert autonomy.loop_running() is True


def test_reconcile_starts_and_stops_loop_from_durable_flag(autonomy, monkeypatch):
    monkeypatch.delenv("NOUS_AUTONOMY_AUTOSTART", raising=False)
    autonomy.enable(30)
    assert autonomy.reconcile(initial_delay=0)["action"] == "running"
    assert _wait_for(autonomy.loop_running)
    autonomy.disable()
    assert autonomy.reconcile()["action"] == "stopped"
    assert _wait_for(lambda: not autonomy.loop_running())


def test_reconcile_respects_autostart_opt_out(autonomy, monkeypatch):
    monkeypatch.setenv("NOUS_AUTONOMY_AUTOSTART", "0")
    autonomy.enable(30)
    assert autonomy.reconcile()["action"] == "autostart_disabled"
    assert autonomy.loop_running() is False


def test_enable_route_starts_managed_loop(monkeypatch):
    from flask import Flask
    from executor import router

    started = []
    monkeypatch.setattr(router, "check_admin_token", lambda _r: True)
    monkeypatch.setattr(router, "service_enable", lambda interval: {"enabled": True, "interval": interval})
    monkeypatch.setattr(router, "service_start_loop", lambda: started.append(True) or {
        "ok": True, "loop_running": True, "loop_mode": "managed_thread", "loop": {"running": True}})
    app = Flask(__name__)
    app.add_url_rule("/remote/service/enable", view_func=router.remote_service_enable_route, methods=["POST"])
    response = app.test_client().post("/remote/service/enable", json={"interval": 60})
    assert response.status_code == 200
    assert response.get_json()["loop_running"] is True
    assert started == [True]


def test_enable_route_rejects_out_of_range_interval(monkeypatch):
    from flask import Flask
    from executor import router

    monkeypatch.setattr(router, "check_admin_token", lambda _r: True)
    def bad(_interval):
        raise ValueError("autonomy_interval_out_of_range")
    monkeypatch.setattr(router, "service_enable", bad)
    app = Flask(__name__)
    app.add_url_rule("/remote/service/enable", view_func=router.remote_service_enable_route, methods=["POST"])
    response = app.test_client().post("/remote/service/enable", json={"interval": 1})
    assert response.status_code == 400


# ----------------------------------------------------------------- N-05 mission actions

@pytest.fixture
def missions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NOUS_DB_PATH", raising=False)
    from executor import mission_system

    module = importlib.reload(mission_system)
    monkeypatch.setattr(module, "FILE", "data/missions.json")
    return module


def test_new_actions_are_allowlisted_and_listed():
    from executor import mission_system, ops_console, auto_mission_executor

    expected = {"search_web", "read_url", "search_memory", "knowledge_search",
                "code_analysis", "app_validation", "agent_task"}
    assert expected <= mission_system.SAFE_TASK_ACTIONS
    assert expected <= set(ops_console.ops_status()["safe_actions"])
    # Unattended runs get read-only actions only; LLM steps and app tests stay manual.
    assert {"search_web", "read_url", "search_memory", "code_analysis"} <= auto_mission_executor.SAFE_AUTO_ACTIONS
    assert "agent_task" not in auto_mission_executor.SAFE_AUTO_ACTIONS
    assert "app_validation" not in auto_mission_executor.SAFE_AUTO_ACTIONS


def test_mission_rejects_missing_or_unknown_payload_fields(missions):
    assert missions.create_mission("x", tasks=[{"action": "search_web"}])["error"] == "missing_query"
    assert missions.create_mission("x", tasks=[{"action": "search_web", "payload": {"query": "a", "shell": "rm"}}])["error"] == "unexpected_payload_field"
    assert missions.create_mission("x", tasks=[{"action": "app_validation", "payload": {"app_name": "../etc"}}])["error"] == "invalid_app_name"


def test_search_web_mission_executes_real_search(missions, monkeypatch):
    from executor import web_search

    seen = []
    monkeypatch.setattr(web_search, "search", lambda q, max_results=5: seen.append(q) or {
        "ok": True, "query": q, "count": 1,
        "results": [{"title": "Kalamata", "url": "https://example.org/k", "snippet": "City in Messenia"}]})
    mission = missions.create_mission("Research", tasks=[{"action": "search_web", "payload": {"query": "Kalamata"}}])
    result = missions.run_next_mission_task(mission["id"])
    assert seen == ["Kalamata"]
    assert result["execution_ok"] is True
    task = result["task"]
    assert task["status"] == "done"
    assert task["result"]["result"]["results"][0]["url"] == "https://example.org/k"
    assert result["mission"]["status"] == "done"


def test_search_web_without_results_fails_the_task(missions, monkeypatch):
    from executor import web_search

    monkeypatch.setattr(web_search, "search", lambda q, max_results=5: {"ok": False, "error": "no_results", "results": []})
    mission = missions.create_mission("Research", tasks=[{"action": "search_web", "payload": {"query": "zzz"}}])
    result = missions.run_next_mission_task(mission["id"])
    assert result["execution_ok"] is False
    assert result["task"]["status"] == "failed"
    assert result["mission"]["status"] == "blocked"


def test_read_url_mission_blocks_unsafe_urls(missions):
    mission = missions.create_mission("Read", tasks=[{"action": "read_url", "payload": {"url": "file:///etc/passwd"}}])
    result = missions.run_next_mission_task(mission["id"])
    assert result["execution_ok"] is False
    assert "unsafe_url" in result["task"]["result"]["result"]["error"]


def test_read_url_mission_reads_public_page(missions, monkeypatch):
    from executor import research_broker, url_reader_engine

    monkeypatch.setattr(research_broker, "validate_url", lambda u: u)
    monkeypatch.setattr(url_reader_engine, "read_url", lambda u, limit=4000: {
        "ok": True, "url": u, "title": "Example", "text": "Real page body text", "chars": 19})
    mission = missions.create_mission("Read", tasks=[{"action": "read_url", "payload": {"url": "https://example.org"}}])
    result = missions.run_next_mission_task(mission["id"])
    assert result["execution_ok"] is True
    assert result["task"]["result"]["result"]["text"] == "Real page body text"


def test_search_memory_mission_returns_stored_knowledge(missions, monkeypatch, tmp_path):
    from executor import knowledge_memory_engine as kme

    monkeypatch.setattr(kme, "KNOWLEDGE_FILE", tmp_path / "data" / "knowledge_memory.json")
    kme.remember_knowledge("Ποια είναι η πρωτεύουσα της Μεσσηνίας", "Η Καλαμάτα είναι η πρωτεύουσα της Μεσσηνίας.",
                           sources=["https://example.org"], kind="document")
    mission = missions.create_mission("Memory", tasks=[{"action": "search_memory", "payload": {"query": "πρωτεύουσα Μεσσηνίας"}}])
    result = missions.run_next_mission_task(mission["id"])
    assert result["execution_ok"] is True
    hits = result["task"]["result"]["result"]["hits"]
    assert hits and "Καλαμάτα" in hits[0]["answer"]
    assert hits[0]["provenance"]["verified"] is False


def test_knowledge_search_combines_documents_and_memory(monkeypatch, tmp_path):
    from executor import knowledge_panel, knowledge_memory_engine as kme, mission_actions

    monkeypatch.setattr(kme, "KNOWLEDGE_FILE", tmp_path / "km.json")
    monkeypatch.setattr(knowledge_panel, "search_documents", lambda q, content_type="", limit=5: [
        {"id": "d1", "documentName": "manual.pdf", "score": 0.81, "text": "Larmor frequency notes"}])
    result = mission_actions.run_mission_action("knowledge_search", {"query": "Larmor"})
    assert result["ok"] is True
    assert result["documents"][0]["document"] == "manual.pdf"


def test_code_analysis_reports_real_metrics_and_blocks_traversal():
    from executor import mission_actions

    result = mission_actions.run_mission_action("code_analysis", {"path": "executor/mission_actions.py"})
    assert result["ok"] is True
    assert result["totals"]["files"] == 1
    assert result["totals"]["functions"] > 5
    assert 0 <= result["quality_score"] <= 100
    blocked = mission_actions.run_mission_action("code_analysis", {"path": "../../etc"})
    assert blocked["ok"] is False and blocked["error"] == "path_outside_repository"


def test_app_validation_runs_isolated_project_tests(monkeypatch, tmp_path):
    from executor import mission_actions

    app = tmp_path / "apps" / "demo-app"
    (app / "tests").mkdir(parents=True)
    (app / "tests" / "test_ok.py").write_text("def test_ok():\n    assert 1 + 1 == 2\n")
    monkeypatch.setenv("NOUS_GENERATED_APPS_DIR", str(tmp_path / "apps"))
    result = mission_actions.run_mission_action("app_validation", {"app_name": "demo-app", "timeout_seconds": 60})
    assert result["ok"] is True, result
    assert result["status"] == "passed"
    assert result["isolation"]["environment_allowlisted"] is True


def test_agent_task_executes_catalog_tool_and_answers(monkeypatch):
    from executor import mission_actions, chat_tools

    monkeypatch.setattr(chat_tools, "dispatch", lambda name, args: {"result": 4})
    replies = iter([
        {"success": True, "response": json.dumps({"tool": "calculate", "input": {"expression": "2+2"}, "summary": "υπολογισμός"})},
        {"success": True, "response": "Το αποτέλεσμα είναι 4."},
    ])
    result = mission_actions.action_agent_task({"goal": "Πόσο κάνει 2+2;"}, planner=lambda turns, system=None: next(replies))
    assert result["ok"] is True
    assert result["tools_completed"] == 1
    assert result["steps"][0] == {"tool": "calculate", "outcome": "completed", "summary": "υπολογισμός"}
    assert "4" in result["answer"]


def test_agent_task_without_llm_fails_honestly():
    from executor import mission_actions

    result = mission_actions.action_agent_task({"goal": "κάνε κάτι"}, planner=lambda turns, system=None: {"success": False})
    assert result["ok"] is False
    assert result["error"] == "agent_step_produced_no_result"


def test_code_quality_standard_mission_uses_real_analysis(missions):
    mission = missions.create_standard_mission("code_quality")
    assert [t["action"] for t in mission["tasks"]] == ["code_analysis", "code_health"]


# ----------------------------------------------------------------- N-06 browser grounding

def _no_browser(monkeypatch, module):
    monkeypatch.setattr(module, "operator_capabilities", lambda: {"browser_driver_ready": False, "node_ready": False})


def test_browser_status_is_honest_on_hosts_without_playwright(monkeypatch):
    from executor import browser_driver_operator as bdo

    _no_browser(monkeypatch, bdo)
    status = bdo.browser_driver_status()
    assert status["ready"] is False
    assert status["host_support"] == "not_available_on_this_host"
    assert status["reason"] == "node_not_installed"
    assert status["fallback"]["engines"] == ["url_reader_engine", "web_search"]


@pytest.mark.parametrize("url", ["file:///etc/passwd", "http://localhost:5000", "http://10.0.0.5/admin",
                                 "http://169.254.169.254/latest/meta-data", "ftp://example.org"])
def test_browser_guard_blocks_local_and_internal_targets(url):
    from executor import browser_driver_operator as bdo

    safe, reason = bdo.guard_url(url)
    assert safe is None and reason
    assert bdo.run_browser_actions(url)["ok"] is False


def test_browser_falls_back_to_url_reader_and_completes(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from executor import browser_driver_operator as bdo, url_reader_engine

    _no_browser(monkeypatch, bdo)
    monkeypatch.setattr(bdo, "validate_url", lambda u: u)
    monkeypatch.setattr(url_reader_engine, "read_url", lambda u: {"ok": True, "title": "T", "text": "body", "chars": 4})
    result = bdo.run_browser_actions("https://example.org", [{"type": "open"}])
    assert result["ok"] is True
    assert result["mode"] == "fallback_url_reader"
    assert result["page"]["text"] == "body"


def test_browser_fallback_never_claims_interactive_actions(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from executor import browser_driver_operator as bdo, url_reader_engine

    _no_browser(monkeypatch, bdo)
    monkeypatch.setattr(bdo, "validate_url", lambda u: u)
    monkeypatch.setattr(url_reader_engine, "read_url", lambda u: {"ok": True, "title": "T", "text": "body"})
    result = bdo.run_browser_actions("https://example.org", [{"type": "click", "selector": "#go"}])
    assert result["ok"] is False
    assert result["error"] == "interactive_actions_not_available_on_this_host"
    assert result["skipped_actions"] == ["click"]


def test_remote_bridge_fulfils_research_jobs_locally(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from executor import browser_driver_operator as bdo, remote_browser_bridge as bridge, url_reader_engine, web_search

    monkeypatch.setattr(bdo, "validate_url", lambda u: u)
    monkeypatch.setattr(url_reader_engine, "read_url", lambda u: {"ok": True, "title": "T", "text": "page"})
    monkeypatch.setattr(web_search, "search", lambda q, max_results=5: {"ok": True, "query": q, "results": [{"url": "https://x.org"}], "count": 1})

    read_job = bridge.create_browser_job("https://example.org")
    assert read_job["status"] == "done" and read_job["fulfilled_by"] == "local_fallback"
    search_job = bridge.create_browser_job("", query="Messenia olive oil")
    assert search_job["status"] == "done" and search_job["result"]["engine"] == "web_search"
    click_job = bridge.create_browser_job("https://example.org", [{"type": "click", "selector": "a"}])
    assert click_job["status"] == "pending_remote_worker"
    assert bridge.complete_browser_job(read_job["id"], {})["error"] == "job_not_pending"

    stored = json.loads(Path(bridge.BRIDGE_FILE).read_text(encoding="utf-8"))
    assert len(stored) == 3
    status = bridge.remote_browser_bridge_status()
    assert status["pending"] == 1 and status["done"] == 2 and status["remote_worker_seen"] is False


def test_remote_bridge_rejects_unsafe_url_job(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from executor import remote_browser_bridge as bridge

    job = bridge.create_browser_job("file:///etc/passwd")
    assert job["status"] == "failed"
    assert "invalid_url" in job["result"]["error"]


# ----------------------------------------------------------------- N-07 knowledge memory

@pytest.fixture
def kme(tmp_path, monkeypatch):
    from executor import knowledge_memory_engine as module

    monkeypatch.setattr(module, "KNOWLEDGE_FILE", tmp_path / "data" / "knowledge_memory.json")
    return module


def test_concurrent_writes_are_atomic_and_lossless(kme):
    errors = []

    def write(i):
        try:
            kme.remember_knowledge(f"question number {i} about olives", f"answer number {i} " * 5, kind="document")
        except Exception as exc:  # pragma: no cover - surfaced via assertion
            errors.append(exc)

    threads = [threading.Thread(target=write, args=(i,)) for i in range(25)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    stored = json.loads(kme.KNOWLEDGE_FILE.read_text(encoding="utf-8"))
    assert len(stored) == 25
    assert not list(kme.KNOWLEDGE_FILE.parent.glob(".knowledge_memory.json.*.tmp"))


def test_item_count_and_answer_size_are_bounded(kme, monkeypatch):
    monkeypatch.setattr(kme, "MAX_KNOWLEDGE_ITEMS", 5)
    for i in range(8):
        kme.remember_knowledge(f"bounded question {i}", f"bounded answer {i}", kind="document")
    assert len(json.loads(kme.KNOWLEDGE_FILE.read_text(encoding="utf-8"))) == 5

    big = kme.remember_knowledge("large answer question", "x" * (kme.MAX_ANSWER_CHARS + 500), kind="document")
    assert len(big["item"]["answer"]) == kme.MAX_ANSWER_CHARS
    assert big["item"]["provenance"]["answer_truncated"] is True
    assert kme.remember_knowledge("q" * (kme.MAX_QUESTION_CHARS + 1), "a")["error"] == "question_too_long"


def test_provenance_and_ttl_recorded_for_web_answers(kme):
    answer = "Η Καλαμάτα βρίσκεται στη Μεσσηνία και είναι γνωστή για τις ελιές της, σύμφωνα με τις πηγές."
    result = kme.learn_from_chat_result("Πού βρίσκεται η Καλαμάτα;", answer, "internet_search",
                                        sources=[{"url": "https://example.org", "title": "Ex"}])
    item = result["item"]
    assert item["provenance"]["origin"] == "chat:internet_search"
    assert item["provenance"]["source_count"] == 1
    assert item["provenance"]["verified"] is False
    assert item["expires_at"] is not None
    assert item["sources"] == [{"url": "https://example.org", "title": "Ex"}]


def test_expired_items_are_not_returned(kme):
    kme.remember_knowledge("expired olive harvest fact", "olive harvest answer text", kind="web", ttl_days=1)
    data = json.loads(kme.KNOWLEDGE_FILE.read_text(encoding="utf-8"))
    data[0]["expires_at"] = "2000-01-01T00:00:00+00:00"
    kme.save_json(kme.KNOWLEDGE_FILE, data)
    assert kme.search_knowledge("olive harvest fact")["hits"] == []


# ----------------------------------------------------------------- F-04 fleet SHA matching

def test_short_sha_prefix_matches_full_sha():
    from executor.fleet_coordinator import versions_match

    full = "0123456789abcdef0123456789abcdef01234567"
    assert versions_match("release", full, "0123456") is True
    assert versions_match("0123456", None, full) is True
    assert versions_match("release", full, full.upper()) is True
    assert versions_match("release", "f" * 64, "fffffff") is True


def test_sha_matching_rejects_ambiguous_or_different_values():
    from executor.fleet_coordinator import versions_match

    full = "0123456789abcdef0123456789abcdef01234567"
    assert versions_match("release", full, "012345") is False      # under 7 chars
    assert versions_match("release", full, "1234567") is False     # not a prefix
    assert versions_match("abcdef1", None, "abcdef2") is False     # two different shorts
    assert versions_match("release-1", None, "release-2") is False


# ----------------------------------------------------------------- N-01 app env isolation

def test_launched_app_receives_only_allowlisted_env(monkeypatch, tmp_path):
    from executor.router import _launch_app_proc

    app_dir = tmp_path.resolve()
    script = app_dir / "main.py"
    script.write_text(
        "import json, os\n"
        "print('ENV:' + json.dumps(sorted(os.environ)))\n"
    )
    monkeypatch.setenv("LANG", "el_GR.UTF-8")
    monkeypatch.setenv("NOUS_FLEET_TOKEN", "fleet-secret")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-secret")
    monkeypatch.setenv("NOUS_TOKEN", "nous-secret")
    monkeypatch.setenv("UNRELATED_SETTING", "x")
    res = _launch_app_proc(f"{sys.executable} {script}", "env_allowlist_app", app_dir)
    res["proc"].wait(timeout=5)
    assert _wait_for(lambda: any(line.startswith("ENV:") for line in res["lines"]))
    line = next(line for line in res["lines"] if line.startswith("ENV:"))
    keys = set(json.loads(line[4:]))
    assert "LANG" in keys
    assert not keys & {"NOUS_FLEET_TOKEN", "GEMINI_API_KEY", "NOUS_TOKEN", "UNRELATED_SETTING"}
    allowed = {"PATH", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED", "HOME", "TMPDIR", "TEMP",
               "LANG", "LC_ALL", "LC_CTYPE", "TZ", "SYSTEMROOT", "WINDIR", "PATHEXT", "LC_CTYPE", "PWD", "SHLVL", "_"}
    assert keys <= allowed, keys - allowed


def test_disable_during_cycle_is_not_overwritten_by_cycle(autonomy, monkeypatch):
    def slow_cycle():
        autonomy.disable()
        return {"ran": True}

    monkeypatch.setattr(autonomy, "run_once", slow_cycle)
    autonomy.enable(30)
    autonomy.run_cycle()
    assert autonomy.status()["enabled"] is False


def test_emergency_stop_during_cycle_is_not_overwritten_by_cycle(autonomy, monkeypatch):
    def stopping_cycle():
        autonomy.emergency_stop("test")
        return {"ran": True}

    monkeypatch.setattr(autonomy, "run_once", stopping_cycle)
    autonomy.enable(30)
    autonomy.run_cycle()
    state = autonomy.status()
    assert state["enabled"] is False and state["emergency_stop"] is True
