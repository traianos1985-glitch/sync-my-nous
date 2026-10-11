import json
import executor.environment_bootstrap as bootstrap


def test_bootstrap_creates_only_known_runtime_directories_and_saves_report(tmp_path):
    (tmp_path / "README.md").write_text("NOUS test fixture", encoding="utf-8")
    report = bootstrap.run_environment_bootstrap(
        tmp_path,
        probe_gemini=False,
        analyze_with_ai=False,
    )

    assert report["status"] == "degraded"
    assert report["checks"]["required_modules"]["ok"] is True
    assert (tmp_path / "data").is_dir()
    assert (tmp_path / "data" / "generated_apps").is_dir()
    assert (tmp_path / "data" / "backups").is_dir()
    assert (tmp_path / "data" / "environment").is_dir()
    assert (tmp_path / "data" / "environment_bootstrap_report.json").is_file()
    assert all(item["action"] == "created_runtime_directory" for item in report["safe_repairs_applied"])
    assert report["gemini"]["status"] == "not_checked"


def test_report_never_contains_token_or_gemini_key_values(tmp_path, monkeypatch):
    token = "NOUS_TOKEN_SHOULD_NEVER_APPEAR_91"
    key = "GEMINI_KEY_SHOULD_NEVER_APPEAR_82"
    monkeypatch.setenv("NOUS_TOKEN", token)
    monkeypatch.setenv("GEMINI_API_KEY", key)

    report = bootstrap.run_environment_bootstrap(
        tmp_path,
        probe_gemini=False,
        analyze_with_ai=False,
    )
    serialized = json.dumps(report)

    assert report["capabilities"]["nous_token_configured"] is True
    assert report["capabilities"]["gemini_key_configured"] is True
    assert token not in serialized
    assert key not in serialized


def test_ai_recommendations_are_review_only_and_source_is_unchanged(tmp_path, monkeypatch):
    (tmp_path / "executor").mkdir()
    source = tmp_path / "executor" / "router.py"
    source.write_text("SENTINEL_SOURCE = True\n", encoding="utf-8")
    monkeypatch.setattr(
        bootstrap,
        "_probe_gemini",
        lambda: {"status": "connected", "connected": True, "model": "test-model"},
    )
    prompts = []

    def ask_llm(prompt):
        prompts.append(prompt)
        return {
            "success": True,
            "provider": "gemini",
            "model": "test-model",
            "response": json.dumps({
                "recommendations": [{
                    "title": "Add deployment health check",
                    "detail": "Verify a live health endpoint after deployment.",
                    "area": "operations",
                    "priority": "high",
                    "safe_to_automate": False,
                    "requires_human_approval": True,
                }],
            }),
        }

    report = bootstrap.run_environment_bootstrap(
        tmp_path,
        probe_gemini=True,
        analyze_with_ai=True,
        ask_llm=ask_llm,
    )

    assert report["ai_assessment"]["status"] == "completed"
    assert report["ai_assessment"]["recommendations"][0]["requires_human_approval"] is True
    assert len(prompts) == 1
    assert "SENTINEL_SOURCE" not in prompts[0]
    assert source.read_text(encoding="utf-8") == "SENTINEL_SOURCE = True\n"


def test_ai_assessment_is_skipped_when_gemini_is_not_connected(tmp_path):
    report = {
        "gemini": {"connected": False},
        "runtime": {},
        "capabilities": {},
        "modules": {},
        "manifest_inventory": {},
        "checks": {},
        "findings": [],
        "safe_repairs_applied": [],
    }
    result = bootstrap._ai_assessment(
        report,
        ask_llm=lambda _prompt: (_ for _ in ()).throw(AssertionError("must not call provider")),
    )
    assert result["status"] == "skipped"
    assert result["recommendations"] == []


def test_recommendation_parser_bounds_and_validates_model_output():
    fence = chr(96) * 3
    raw = fence + "json\n" + json.dumps({
        "recommendations": [
            {
                "title": "  Improve observability  ",
                "detail": "Add a structured runtime event.",
                "priority": "HIGH",
                "area": "logging",
                "safe_to_automate": True,
                "requires_human_approval": False,
            },
            {"title": "", "detail": "invalid"},
            "not an object",
        ],
    }) + "\n" + fence
    parsed = bootstrap._parse_ai_recommendations(raw)
    assert len(parsed) == 1
    assert parsed[0]["title"] == "Improve observability"
    assert parsed[0]["priority"] == "high"
    assert parsed[0]["safe_to_automate"] is True
    assert parsed[0]["requires_human_approval"] is False


def test_status_returns_not_started_when_report_does_not_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap, "_LAST_RESULT", None)
    status = bootstrap.environment_bootstrap_status(tmp_path)
    assert status["status"] == "not_started"
    assert status["report_available"] is False
