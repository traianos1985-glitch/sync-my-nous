import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
import pytest

from executor.nous_drive import create_data_backup
from executor.browser_driver_operator import run_browser_actions, create_playwright_script


def test_create_data_backup_sqlite_consistency_and_rotation(monkeypatch, tmp_path):
    # Setup temporary directory for data and backups
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_file = data_dir / "test_store.db"
    json_file = data_dir / "info.json"

    # Create dummy SQLite database
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE records (id INTEGER PRIMARY KEY, note TEXT)")
    conn.execute("INSERT INTO records (note) VALUES ('hello nous')")
    conn.commit()
    conn.close()

    json_file.write_text('{"status": "active"}', encoding="utf-8")

    # Run backup 12 times to test creation and max rotation (limit = 3)
    logs = []
    for i in range(5):
        bpath, size_mb = create_data_backup(max_backups=3, log_fn=lambda m: logs.append(m))
        assert bpath.exists()
        assert (bpath / "test_store.db").exists()
        assert (bpath / "info.json").exists()

        # Verify sqlite file is healthy and readable
        check_conn = sqlite3.connect(str(bpath / "test_store.db"))
        row = check_conn.execute("SELECT note FROM records").fetchone()
        assert row[0] == "hello nous"
        check_conn.close()

    # Ensure rotation kept only 3 snapshots
    backup_dir = tmp_path / "data" / "backups"
    existing_backups = list(backup_dir.glob("nous_data_*"))
    assert len(existing_backups) == 3


def test_browser_driver_url_guard():
    # Private / local URLs must be rejected before attempting execution
    res1 = run_browser_actions("file:///etc/passwd")
    assert not res1["ok"]
    assert "invalid_url" in res1["error"]

    res2 = run_browser_actions("http://127.0.0.1:8080")
    assert not res2["ok"]
    assert "invalid_url" in res2["error"]

    res3 = run_browser_actions("http://localhost/secret")
    assert not res3["ok"]
    assert "invalid_url" in res3["error"]
