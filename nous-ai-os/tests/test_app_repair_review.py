from executor.app_repair_review import (
    review_repair_proposal,
    save_repair_proposal,
)


def _diagnosis(app_name, changes, hashes=None):
    return {
        "ok": True,
        "status": "proposal_ready",
        "app_name": app_name,
        "summary": "Example repair",
        "root_causes": [],
        "validation_plan": ["Run tests after human review"],
        "risks": [],
        "changes": changes,
        "change_validation_errors": [],
        "context_files": list((hashes or {}).keys()),
        "baseline_hashes": hashes or {},
        "writes_performed": False,
        "human_review_required": True,
    }


def test_save_and_review_python_proposal_without_writing_app_files(tmp_path):
    root = tmp_path / "apps"
    app = root / "sample_app"
    app.mkdir(parents=True)
    original = "def answer():\n    return 41\n"
    target = app / "main.py"
    target.write_text(original, encoding="utf-8")
    import hashlib
    baseline = hashlib.sha256(original.encode()).hexdigest()
    store = tmp_path / "data" / "repairs.json"

    saved = save_repair_proposal(
        "sample_app", root,
        _diagnosis(
            "sample_app",
            [
                {"path": "sample_app/main.py", "content": "def answer():\n    return 42\n"},
                {"path": "sample_app/tests/test_main.py", "content": "def test_answer():\n    assert True\n"},
            ],
            {"sample_app/main.py": baseline},
        ),
        store,
    )
    assert saved["ok"] is True
    report = review_repair_proposal(saved["repair_id"], root, store)
    assert report["ok"] is True
    assert report["ready_for_human_review"] is True
    assert report["writes_performed"] is False
    assert report["tests_executed"] is False
    assert report["proposal_applied"] is False
    assert target.read_text(encoding="utf-8") == original
    assert (app / "tests" / "test_main.py").exists() is False


def test_preflight_blocks_python_syntax_error(tmp_path):
    root = tmp_path / "apps"
    app = root / "sample_app"
    app.mkdir(parents=True)
    original = "pass\n"
    (app / "main.py").write_text(original, encoding="utf-8")
    import hashlib
    store = tmp_path / "repairs.json"
    saved = save_repair_proposal(
        "sample_app", root,
        _diagnosis(
            "sample_app",
            [{"path": "sample_app/main.py", "content": "def broken(:\n"}],
            {"sample_app/main.py": hashlib.sha256(original.encode()).hexdigest()},
        ),
        store,
    )
    report = review_repair_proposal(saved["repair_id"], root, store)
    assert report["ready_for_human_review"] is False
    assert any(item.startswith("python_syntax:sample_app/main.py") for item in report["blockers"])


def test_preflight_blocks_stale_baseline(tmp_path):
    root = tmp_path / "apps"
    app = root / "sample_app"
    app.mkdir(parents=True)
    target = app / "main.py"
    target.write_text("pass\n", encoding="utf-8")
    import hashlib
    store = tmp_path / "repairs.json"
    saved = save_repair_proposal(
        "sample_app", root,
        _diagnosis(
            "sample_app",
            [{"path": "sample_app/main.py", "content": "print('updated')\n"}],
            {"sample_app/main.py": hashlib.sha256(b"pass\n").hexdigest()},
        ),
        store,
    )
    target.write_text("print('someone changed this')\n", encoding="utf-8")
    report = review_repair_proposal(saved["repair_id"], root, store)
    assert report["ready_for_human_review"] is False
    assert "stale_baseline:sample_app/main.py" in report["blockers"]


def test_preflight_blocks_invalid_json_and_warns_for_dependencies(tmp_path):
    root = tmp_path / "apps"
    app = root / "sample_app"
    app.mkdir(parents=True)
    store = tmp_path / "repairs.json"
    saved = save_repair_proposal(
        "sample_app", root,
        _diagnosis(
            "sample_app",
            [
                {"path": "sample_app/package.json", "content": "{bad json"},
                {"path": "sample_app/requirements.txt", "content": "flask==3.0.0\n"},
            ],
        ),
        store,
    )
    assert saved["ok"] is True
    report = review_repair_proposal(saved["repair_id"], root, store)
    assert report["ready_for_human_review"] is False
    assert "json_syntax:sample_app/package.json" in report["blockers"]
    assert "dependency_change_requires_dependency_and_lockfile_review" in report["warnings"]


def test_save_rejects_unsafe_or_unsupported_changes(tmp_path):
    root = tmp_path / "apps"
    (root / "sample_app").mkdir(parents=True)
    diagnosis = _diagnosis(
        "sample_app",
        [
            {"path": "sample_app/../escape.py", "content": "pass"},
            {"path": "sample_app/payload.exe", "content": "binary"},
        ],
    )
    result = save_repair_proposal("sample_app", root, diagnosis, tmp_path / "repairs.json")
    assert result["ok"] is False
    assert result["error"] in {"invalid_proposed_changes", "unsupported_file_type"}


def test_review_rejects_unknown_repair_id(tmp_path):
    assert review_repair_proposal("repair_" + "a" * 32, tmp_path, tmp_path / "missing.json") == {
        "ok": False,
        "error": "repair_not_found",
    }
