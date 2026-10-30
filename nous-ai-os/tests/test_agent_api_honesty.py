"""Operational agent APIs must not claim work or verification that never happened."""
from flask import Flask

from executor.react_agent import ReActAgent, ToolRegistry
from executor.swarm_orchestrator import run_swarm

FABRICATED_PHRASES = (
    "Syntax checks passed", "Safety filters confirmed", "Unit tests operational",
    "Code operations executed", "Validated environment and dependency availability",
)


def test_swarm_declares_simulation_and_executes_nothing():
    result = run_swarm("Refactor router and run test suite")
    assert result["simulated"] is True and result["executed"] is False
    assert "simulated" in result["notice"].lower()
    assert result["status"] == "completed" and result["agent_count"] == 4


def test_swarm_trace_contains_no_fabricated_results():
    trace = run_swarm("Refactor router")["trace"]
    assert {step["role"] for step in trace} == {"architect", "researcher", "coder", "reviewer"}
    assert all(step["simulated"] is True and step["executed"] is False for step in trace)
    flattened = repr(trace)
    for phrase in FABRICATED_PHRASES:
        assert phrase not in flattened
    reviewer = next(step for step in trace if step["role"] == "reviewer")
    assert reviewer["status"] == "not_run" and reviewer["score"] is None
    assert reviewer["verifications"] == []


def test_react_inspection_reports_real_mode_and_step_count():
    agent = ReActAgent(registry=ToolRegistry())
    result = agent.run("list the files", max_steps=5)
    assert result["mode"] == "single_step_inspection"
    assert result["steps_executed"] == len(result["steps"]) == 1
    assert result["max_steps_requested"] == 5


def test_react_max_steps_is_sanitised():
    agent = ReActAgent(registry=ToolRegistry())
    assert agent.run("list", max_steps="abc")["max_steps_requested"] == 5
    assert agent.run("list", max_steps=99)["max_steps_requested"] == 5
    assert agent.run("list", max_steps=0)["max_steps_requested"] == 1
    assert agent.run("list", max_steps=None)["max_steps_requested"] == 5


def test_swarm_endpoint_exposes_simulation_flags(monkeypatch):
    from executor.blueprints import agent_ops_bp as module
    monkeypatch.setattr(module, "check_admin_token", lambda _request: True)
    app = Flask(__name__)
    app.register_blueprint(module.agent_ops_bp)
    response = app.test_client().post("/api/ops/swarm/run", json={"mission": "demo"})
    body = response.get_json()
    assert response.status_code == 200
    assert body["result"]["simulated"] is True
    assert body["result"]["executed"] is False
