from executor.agent_core import DEFAULT_AGENT, AgentCore, AuditPlugin
from executor.agent_registry import LEGACY_MODULES, get_core


def test_canonical_core_requires_approval_and_audits():
    result = AgentCore([AuditPlugin()]).run("inspect repository")
    assert result["ok"] is True
    assert result["approval_required"] is True
    assert result["audit"]["phase"] == "after_run"


def test_registry_exposes_one_core_and_compatibility_adapters():
    assert get_core() is DEFAULT_AGENT
    assert {item.name for item in LEGACY_MODULES} == {
        "autonomous",
        "research",
        "scheduler",
        "browser",
        "repair",
    }
