import json
from pathlib import Path

from executor import technical_intelligence as intelligence


def test_collect_dependencies_reads_manifests_without_running_package_managers(tmp_path, monkeypatch):
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"react": "^18.0.0"}, "devDependencies": {"vite": "^5.0.0"}}),
        encoding="utf-8",
    )
    (tmp_path / "package-lock.json").write_text(
        json.dumps({
            "packages": {
                "node_modules/react": {"version": "18.2.0"},
                "node_modules/vite": {"version": "5.4.0"},
            }
        }),
        encoding="utf-8",
    )
    (tmp_path / "nous-ai-os").mkdir()
    (tmp_path / "nous-ai-os" / "requirements.txt").write_text(
        "requests>=2.0\nflask>=3.0\n# ignored\n-e git+https://example.invalid/repo.git\n",
        encoding="utf-8",
    )
    (tmp_path / "nous-ai-os" / "requirements-dev.txt").write_text(
        "pytest>=8.0\nrequests>=2.1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(intelligence, "_installed_python_version", lambda name: "2.32.0")

    found = intelligence.collect_dependencies(tmp_path)

    by_name = {(item["ecosystem"], item["name"]): item for item in found}
    assert by_name[("npm", "react")]["current_version"] == "18.2.0"
    assert by_name[("npm", "vite")]["declared"] == "^5.0.0"
    assert by_name[("pypi", "requests")]["current_version"] == "2.32.0"
    assert "git+https" not in " ".join(item["name"] for item in found)
    assert len([item for item in found if item["ecosystem"] == "pypi" and item["name"] == "requests"]) == 1


def test_version_classification_is_conservative():
    assert intelligence._update_kind("1.2.3", "2.0.0") == "major_update"
    assert intelligence._update_kind("1.2.3", "1.3.0") == "minor_update"
    assert intelligence._update_kind("1.2.3", "1.2.4") == "patch_update"
    assert intelligence._update_kind("1.2.3", "1.2.3") == "up_to_date"
    assert intelligence._update_kind(None, "1.2.3") == "version_unknown"
    assert intelligence._update_kind("2.0.0", "1.9.9") == "current_newer_than_registry"


def test_scan_selection_does_not_starve_python_dependencies():
    dependencies = [
        {"ecosystem": "npm", "name": f"npm-{index}"} for index in range(50)
    ] + [
        {"ecosystem": "pypi", "name": f"python-{index}"} for index in range(8)
    ]

    selected = intelligence._select_dependencies(dependencies, 40)

    assert len(selected) == 40
    assert {item["ecosystem"] for item in selected} == {"npm", "pypi"}
    assert sum(item["ecosystem"] == "pypi" for item in selected) == 8


def test_scan_reports_updates_and_never_claims_to_install(monkeypatch, tmp_path):
    dependencies = [
        {
            "ecosystem": "npm",
            "name": "react",
            "current_version": "18.2.0",
            "declared": "^18.0.0",
            "manifest": "package.json",
            "registry_url": "https://registry.npmjs.org/react/latest",
            "package_url": "https://www.npmjs.com/package/react",
        },
        {
            "ecosystem": "pypi",
            "name": "requests",
            "current_version": "2.31.0",
            "declared": ">=2.0",
            "manifest": "nous-ai-os/requirements.txt",
            "registry_url": "https://pypi.org/pypi/requests/json",
            "package_url": "https://pypi.org/project/requests/",
        },
    ]
    monkeypatch.setattr(intelligence, "collect_dependencies", lambda: dependencies)
    monkeypatch.setattr(intelligence, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(intelligence, "REPORT_PATH", tmp_path / "data" / "report.json")
    monkeypatch.setattr(intelligence, "HISTORY_PATH", tmp_path / "data" / "history.json")

    def fake_latest(dependency):
        latest = {"react": "19.0.0", "requests": "2.32.0"}[dependency["name"]]
        return {"ok": True, "latest_version": latest}

    monkeypatch.setattr(intelligence, "_fetch_latest", fake_latest)
    report = intelligence.run_scan(limit=2)

    assert report["ok"] is True
    assert report["status"] == "complete"
    assert report["update_count"] == 2
    assert report["dependency_count"] == 2
    assert report["scanned_count"] == 2
    assert report["major_update_count"] == 1
    assert all(item["action"] == "proposal_only" for item in report["updates"])
    assert report["safety"]["package_installs_performed"] == 0
    assert report["safety"]["source_files_modified"] == 0
    assert json.loads((tmp_path / "data" / "report.json").read_text(encoding="utf-8"))["update_count"] == 2
    assert len(json.loads((tmp_path / "data" / "history.json").read_text(encoding="utf-8"))) == 1


def test_scan_rejects_invalid_limit(monkeypatch):
    for value in (0, -1, True, 61, "5"):
        result = intelligence.run_scan(value)
        assert result["ok"] is False
        assert result["error"] == "invalid_limit"


def test_registry_fetcher_rejects_untrusted_registry_url(monkeypatch):
    dependency = {
        "ecosystem": "npm",
        "name": "react",
        "registry_url": "http://127.0.0.1:3000/latest",
    }
    monkeypatch.setattr(
        intelligence.requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network must not be called")),
    )
    result = intelligence._fetch_latest(dependency)
    assert result == {"ok": False, "error": "registry_url_not_allowed"}


def test_registry_fetcher_does_not_follow_redirects(monkeypatch):
    class FakeResponse:
        status_code = 302
        headers = {}
        closed = False

        def close(self):
            self.closed = True

    response = FakeResponse()
    captured = {}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        return response

    monkeypatch.setattr(intelligence.requests, "get", fake_get)
    result = intelligence._fetch_latest({
        "ecosystem": "npm",
        "name": "react",
        "registry_url": "https://registry.npmjs.org/react/latest",
    })
    assert result == {"ok": False, "error": "registry_http_302"}
    assert captured["allow_redirects"] is False
    assert response.closed is True


def test_proposals_only_return_verified_updates(monkeypatch, tmp_path):
    monkeypatch.setattr(intelligence, "REPORT_PATH", tmp_path / "report.json")
    (tmp_path / "report.json").write_text(json.dumps({
        "checked_at": 123,
        "status": "partial",
        "updates": [
            {"name": "react", "kind": "major_update", "source_url": "https://www.npmjs.com/package/react"},
        ],
    }), encoding="utf-8")

    result = intelligence.list_proposals()

    assert result["ok"] is True
    assert result["count"] == 1
    assert result["proposals"][0]["name"] == "react"
    assert "Δεν έγινε εγκατάσταση" in result["note"]
    assert intelligence.list_proposals(0)["error"] == "invalid_limit"
