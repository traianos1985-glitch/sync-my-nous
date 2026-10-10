import importlib
import json
from pathlib import Path

import pytest

from executor import review_inbox_manager


@pytest.mark.parametrize("raw", [b'{"broken":', b'{"not":"a list"}', b'[{"valid":true}, 7]'])
def test_review_inbox_fails_closed_without_overwrite(tmp_path, monkeypatch, raw):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(review_inbox_manager)
    monkeypatch.setattr(module, "PENDING_REVIEWS", Path("data/pending_reviews.json"))
    monkeypatch.setattr(module, "REPORTS", Path("data/reports"))
    Path("data").mkdir()
    store = Path("data/pending_reviews.json")
    store.write_bytes(raw)

    with pytest.raises(RuntimeError, match="json_state_integrity_failure"):
        module.run_review_inbox_manager()

    assert store.read_bytes() == raw


def test_review_inbox_deduplicates_and_persists_defaults_atomically(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(review_inbox_manager)
    monkeypatch.setattr(module, "PENDING_REVIEWS", Path("data/pending_reviews.json"))
    monkeypatch.setattr(module, "REPORTS", Path("data/reports"))
    Path("data").mkdir()
    store = Path("data/pending_reviews.json")
    duplicate = {"kind": "patch", "proposal_id": "p-1", "title": "Patch"}
    store.write_text(json.dumps([duplicate, duplicate]), encoding="utf-8")

    report = module.run_review_inbox_manager()

    persisted = json.loads(store.read_text(encoding="utf-8"))
    assert report["before"] == 2
    assert report["after"] == 1
    assert report["removed_duplicates"] == 1
    assert persisted[0]["status"] == "pending"
    assert persisted[0]["created_at"]
    assert Path(report["report_path"]).is_file()


def test_review_inbox_concurrent_runs_keep_valid_json(tmp_path, monkeypatch):
    # The stable sidecar lock and atomic replace must leave a readable list.
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(review_inbox_manager)
    monkeypatch.setattr(module, "PENDING_REVIEWS", Path("data/pending_reviews.json"))
    monkeypatch.setattr(module, "REPORTS", Path("data/reports"))
    Path("data").mkdir()
    Path("data/pending_reviews.json").write_text(
        json.dumps([{"kind": "mission", "mission_id": "m-1", "title": "Review"}]),
        encoding="utf-8",
    )

    module.run_review_inbox_manager()
    assert isinstance(json.loads(Path("data/pending_reviews.json").read_text(encoding="utf-8")), list)
