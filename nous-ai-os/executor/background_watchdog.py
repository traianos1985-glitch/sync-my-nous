"""Autonomous Background Watchdog & Nightly Maintenance Daemon for NOUS.

Inspects git repository status, optimizes and vacuums SQLite storage,
monitors resource health, and performs self-maintenance.
"""
import os
import sqlite3
import subprocess
import time
from typing import Any, Dict

DB_PATH = "data/nous_storage.db"

class BackgroundWatchdog:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def check_git_health(self) -> Dict[str, Any]:
        """Checks if the working tree has uncommitted changes or detached state."""
        try:
            res = subprocess.run(
                "git status --porcelain", shell=True, capture_output=True, text=True, timeout=5
            )
            dirty_files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            branch_res = subprocess.run(
                "git rev-parse --abbrev-ref HEAD", shell=True, capture_output=True, text=True, timeout=5
            )
            branch = branch_res.stdout.strip() or "unknown"
            return {
                "branch": branch,
                "clean": len(dirty_files) == 0,
                "uncommitted_files": dirty_files[:20]
            }
        except Exception as e:
            return {"branch": "unknown", "clean": False, "error": str(e)}

    def optimize_database(self) -> Dict[str, Any]:
        """Cleans stale rows and vacuums the SQLite storage."""
        if not os.path.exists(self.db_path):
            return {"status": "no_db", "cleaned": 0}

        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            with conn:
                # Keep last 500 in memories
                conn.execute("""
                    DELETE FROM memories WHERE id NOT IN (
                        SELECT id FROM memories ORDER BY id DESC LIMIT 500
                    )
                """)
                # Vacuum
                conn.execute("VACUUM")
            conn.close()
            return {"status": "optimized", "vacuum": True, "db_size_bytes": os.path.getsize(self.db_path)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_health_cycle(self) -> Dict[str, Any]:
        """Runs a complete self-maintenance health check."""
        start = time.time()
        git_info = self.check_git_health()
        db_info = self.optimize_database()
        
        status = "healthy"
        if not git_info.get("clean", True):
            status = "attention_needed"

        return {
            "status": status,
            "timestamp": time.time(),
            "duration_s": round(time.time() - start, 3),
            "git": git_info,
            "database": db_info
        }

DEFAULT_WATCHDOG = BackgroundWatchdog()

def run_watchdog_check() -> Dict[str, Any]:
    return DEFAULT_WATCHDOG.run_health_cycle()
