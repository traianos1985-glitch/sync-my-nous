import json

from executor import app_builder
from executor.engineering_standards import CODE_CHANGE_ENGINEERING_GUIDE, validate_app_plan
from executor.patch_proposal_enricher import build_patch_draft


def valid_plan():
    return {
        "app_name": "sample_app",
        "title": "Sample App",
        "description": "A small but complete application.",
        "tech_stack": ["Python"],
        "files": [
            {
                "path": "sample_app/main.py",
                "description": "Entrypoint",
                "content": "def main():\n    return {'ok': True}\n",
            },
            {
                "path": "sample_app/tests/test_main.py",
                "description": "Regression tests",
                "content": "def test_main():\n    assert True\n",
            },
            {
                "path": "sample_app/README.md",
                "description": "Usage and setup",
                "content": "# Sample App\n\nSetup and test instructions.\n",
            },
        ],
        "run_command": "python main.py",
        "install_notes": "",
        "notes": "No external services required.",
    }


def test_accepts_complete_multi_file_application_plan():
    assert validate_app_plan(valid_plan()) == []


def test_requires_readme_tests_and_entrypoint():
    plan = valid_plan()
    plan["files"] = [
        {"path": "sample_app/notes.txt", "content": "notes"},
        {"path": "sample_app/tests/test_main.py", "content": "def test_ok(): pass"},
    ]

    errors = validate_app_plan(plan)

    assert "missing_readme" in errors
    assert "missing_application_entrypoint" in errors
    assert "files_must_contain_2_to_80_entries" not in errors


def test_rejects_unsafe_and_duplicate_paths():
    plan = valid_plan()
    plan["files"].append({
        "path": "sample_app/../outside.py",
        "content": "unsafe",
    })
    plan["files"].append({
        "path": "sample_app/README.md",
        "content": "duplicate",
    })

    errors = validate_app_plan(plan)

    assert any(error.endswith("_unsafe_path") for error in errors)
    assert "duplicate_path:sample_app/README.md" in errors


def test_rejects_invalid_app_slug_and_non_object_plan():
    assert validate_app_plan([]) == ["plan_must_be_object"]
    assert validate_app_plan({**valid_plan(), "app_name": "../outside"}) == [
        "invalid_app_name"
    ]


def test_rejects_oversized_generated_files():
    plan = valid_plan()
    plan["files"][0]["content"] = "x" * 250_001

    assert "file_too_large:sample_app/main.py" in validate_app_plan(plan)


def test_plan_app_does_not_queue_unvalidated_llm_output(monkeypatch, tmp_path):
    queue = tmp_path / "data" / "app_builder_queue.json"
    monkeypatch.setattr(app_builder, "QUEUE", queue)
    monkeypatch.setattr(
        "executor.remote_llm.ask_remote_llm",
        lambda prompt: {
            "success": True,
            "response": json.dumps({
                "app_name": "sample_app",
                "title": "Broken Plan",
                "description": "No tests or readme",
                "files": [
                    {"path": "sample_app/main.py", "content": "print('hello')"}
                ],
            }),
        },
    )

    result = app_builder.plan_app("Build a real application")

    assert result["ok"] is False
    assert result["error"] == "app_plan_validation_failed"
    assert "missing_readme" in result["validation_errors"]
    assert not queue.exists()


def test_plan_app_queues_validated_plan_for_human_approval(monkeypatch, tmp_path):
    queue = tmp_path / "data" / "app_builder_queue.json"
    monkeypatch.setattr(app_builder, "QUEUE", queue)
    monkeypatch.setattr(
        "executor.remote_llm.ask_remote_llm",
        lambda prompt: {
            "success": True,
            "response": json.dumps(valid_plan()),
        },
    )

    result = app_builder.plan_app("Build a sample application")

    assert result["ok"] is True
    plan = result["plan"]
    assert plan["status"] == "pending_approval"
    assert plan["engineering_validation"]["ok"] is True
    assert plan["engineering_validation"]["runtime_tests_executed"] is False
    assert len(json.loads(queue.read_text(encoding="utf-8"))) == 1


def test_plan_app_rejects_empty_and_oversized_descriptions(monkeypatch):
    def unexpected_call(_prompt):
        raise AssertionError("LLM must not be called for invalid descriptions")

    monkeypatch.setattr("executor.remote_llm.ask_remote_llm", unexpected_call)

    assert app_builder.plan_app("  ")["error"] == "empty_description"
    result = app_builder.plan_app("x" * 8001)
    assert result["error"] == "description_too_long"



def test_code_upgrade_drafts_include_reviewable_engineering_expectations():
    draft = build_patch_draft({
        "analysis": {
            "root_cause": "Route contract mismatch",
            "candidate_files": ["executor/router.py"],
        }
    })

    assert draft["engineering_standard"] == CODE_CHANGE_ENGINEERING_GUIDE
    assert "add_focused_regression_tests" in draft["validation_expectations"]
    assert "require_human_review_before_apply" in draft["validation_expectations"]
