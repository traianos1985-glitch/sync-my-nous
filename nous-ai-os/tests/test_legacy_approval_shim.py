import pytest

from executor.approval import ask_approval


def test_legacy_interactive_approval_fails_closed_without_reading_stdin(monkeypatch):
    def unexpected_input(*_args, **_kwargs):
        pytest.fail("server-side approval must never block on stdin")

    monkeypatch.setattr("builtins.input", unexpected_input)
    with pytest.raises(RuntimeError, match="interactive_approval_removed"):
        ask_approval("deploy")
