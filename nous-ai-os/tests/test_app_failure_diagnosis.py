import json

from executor.app_failure_diagnosis import (
    _redact_source,
    _validate_changes,
    collect_project_context,
    diagnose_test_failure,
)


def test_collect_context_excludes_env_and_skips_large_or_unreadable_files(tmp_path):
    root = tmp_path / "apps"
    app = root / "sample_app"
    app.mkdir(parents=True)
    (app / "main.py").write_text("print('safe')", encoding="utf-8")
    (app / ".env").write_text("API_KEY=secret", encoding="utf-8")
    (app / ".env.example").write_text("API_KEY=placeholder", encoding="utf-8")
    result = collect_project_context("sample_app", root)
    assert result["ok"] is True
    assert [item["path"] for item in result["files"]] == ["sample_app/main.py"]
    assert "secret" not in json.dumps(result["files"])


def test_collect_context_rejects_invalid_app_name_and_missing_app(tmp_path):
    assert collect_project_context("../escape", tmp_path)["error"] == "invalid_app_name"
    assert collect_project_context("sample_app", tmp_path)["error"] == "app_not_found"


def test_validate_changes_accepts_only_app_relative_safe_files():
    changes, errors = _validate_changes(
        "sample_app",
        [
            {"path": "sample_app/main.py", "content": "print('ok')"},
            {"path": "sample_app/../outside.py", "content": "bad"},
            {"path": "sample_app/.env", "content": "secret"},
            {"path": "/sample_app/main.py", "content": "bad"},
        ],
    )
    assert changes == [{"path": "sample_app/main.py", "content": "print('ok')"}]
    assert len(errors) == 3


def test_diagnosis_requires_a_failed_test_result(tmp_path):
    assert diagnose_test_failure(
        "sample_app", tmp_path, {"ok": True, "status": "passed"}
    )["error"] == "failed_test_result_required"


def test_diagnosis_returns_validated_review_only_proposal(tmp_path):
    root = tmp_path / "apps"
    app = root / "sample_app"
    app.mkdir(parents=True)
    (app / "main.py").write_text("def answer(): return 41", encoding="utf-8")
    (app / "tests").mkdir()
    (app / "tests" / "test_main.py").write_text("assert answer() == 42", encoding="utf-8")
    seen = []

    def fake_llm(prompt):
        seen.append(prompt)
        return {
            "success": True,
            "response": json.dumps({
                "summary": "The function returns the wrong value.",
                "root_causes": [{"cause": "Off-by-one", "evidence": "main.py", "confidence": "high"}],
                "validation_plan": ["Run pytest -q tests"],
                "risks": [],
                "changes": [{"path": "sample_app/main.py", "content": "def answer(): return 42"}],
            }),
        }

    result = diagnose_test_failure(
        "sample_app", root,
        {"ok": False, "status": "failed", "stdout": "assert 41 == 42", "stderr": ""},
        ask_llm=fake_llm,
    )
    assert result["ok"] is True
    assert result["status"] == "proposal_ready"
    assert result["writes_performed"] is False
    assert result["tests_rerun"] is False
    assert result["human_review_required"] is True
    assert result["changes"][0]["path"] == "sample_app/main.py"
    assert "assert 41 == 42" in seen[0]
    assert (app / "main.py").read_text(encoding="utf-8") == "def answer(): return 41"


def test_diagnosis_rejects_invalid_llm_json_and_does_not_write(tmp_path):
    root = tmp_path / "apps"
    app = root / "sample_app"
    app.mkdir(parents=True)
    (app / "main.py").write_text("pass", encoding="utf-8")
    result = diagnose_test_failure(
        "sample_app", root, {"ok": False, "status": "failed"},
        ask_llm=lambda _prompt: {"success": True, "response": "not json"},
    )
    assert result == {"ok": False, "error": "invalid_diagnosis_response"}


def test_redacts_obvious_hardcoded_credentials_from_source():
    source = 'API_KEY=sk_live_123456789\nTOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890'
    redacted = _redact_source(source)
    assert 'sk_live_123456789' not in redacted
    assert 'ghp_abcdefghijklmnopqrstuvwxyz1234567890' not in redacted
    assert '[REDACTED]' in redacted


def test_context_includes_original_file_fingerprints_for_stale_review(tmp_path):
    import hashlib

    root = tmp_path / "apps"
    app = root / "sample_app"
    app.mkdir(parents=True)
    source = "print('review me')\\n"
    (app / "main.py").write_text(source, encoding="utf-8")
    result = collect_project_context("sample_app", root)
    assert result["baseline_hashes"]["sample_app/main.py"] == hashlib.sha256(source.encode()).hexdigest()
