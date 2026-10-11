"""Bounded subprocess test runner for reviewed generated Python applications.

This is process isolation with resource limits, not a security sandbox: it does not
block network access or guarantee containment from a hostile operating system process.
Only use it for applications that have passed human review. Do not auto-install deps.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

_MAX_TIMEOUT_SECONDS = 300
_MAX_OUTPUT_CHARS = 12_000
_APP_SLUG = re.compile(r"^[a-z][a-z0-9_-]{0,59}$")


def _limit_child_resources() -> None:
    """Apply best-effort POSIX resource limits in the child before pytest starts."""
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
        resource.setrlimit(resource.RLIMIT_FSIZE, (20 * 1024 * 1024, 20 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        if hasattr(resource, "RLIMIT_CORE"):
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (ImportError, OSError, ValueError):
        # Windows and restricted runtimes may not expose POSIX limits.
        return


def run_project_tests(
    app_name: str,
    apps_root: str | Path,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Run an existing project's tests without shell expansion or dependency install."""
    if not isinstance(app_name, str) or not _APP_SLUG.fullmatch(app_name):
        return {"ok": False, "error": "invalid_app_name"}
    try:
        timeout = int(timeout_seconds)
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid_timeout"}
    if not 1 <= timeout <= _MAX_TIMEOUT_SECONDS:
        return {
            "ok": False,
            "error": "timeout_out_of_range",
            "max_timeout_seconds": _MAX_TIMEOUT_SECONDS,
        }

    root = Path(apps_root).resolve()
    project = (root / app_name).resolve()
    if project == root or root not in project.parents:
        return {"ok": False, "error": "path_outside_apps_directory"}
    if not project.is_dir():
        return {"ok": False, "error": "app_not_found"}
    tests_dir = project / "tests"
    if not tests_dir.is_dir():
        return {"ok": False, "error": "automated_tests_not_found"}
    try:
        tests_dir.resolve().relative_to(project)
    except ValueError:
        return {"ok": False, "error": "unsafe_test_path"}
    test_files = [
        item for item in tests_dir.rglob("*")
        if item.is_file()
        and (item.name.startswith("test_") or ".test." in item.name or ".spec." in item.name)
    ]
    if not test_files:
        return {"ok": False, "error": "automated_tests_not_found"}
    for test_file in test_files:
        try:
            test_file.resolve().relative_to(project)
        except ValueError:
            return {"ok": False, "error": "unsafe_test_path", "path": test_file.name}

    # Keep credentials and unrelated service configuration out of the test process.
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    }
    for key in ("SYSTEMROOT", "WINDIR", "PATHEXT"):
        if key in os.environ:
            env[key] = os.environ[key]

    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="nous-test-home-") as home:
            env["HOME"] = home
            env["TMPDIR"] = home
            env["TEMP"] = home
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "tests"],
                cwd=str(project),
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
                close_fds=True,
                preexec_fn=_limit_child_resources if os.name == "posix" else None,
            )
        stdout = (completed.stdout or "")[-_MAX_OUTPUT_CHARS:]
        stderr = (completed.stderr or "")[-_MAX_OUTPUT_CHARS:]
        return {
            "ok": completed.returncode == 0,
            "status": "passed" if completed.returncode == 0 else "failed",
            "return_code": completed.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "command": [sys.executable, "-m", "pytest", "-q", "tests"],
            "stdout": stdout,
            "stderr": stderr,
            "output_truncated": len(completed.stdout or "") > _MAX_OUTPUT_CHARS
            or len(completed.stderr or "") > _MAX_OUTPUT_CHARS,
            "isolation": {
                "subprocess": True,
                "timeout_seconds": timeout,
                "resource_limits": os.name == "posix",
                "environment_allowlisted": True,
                "network_blocked": False,
                "security_sandbox": False,
            },
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "status": "timeout",
            "error": "test_timeout",
            "timeout_seconds": timeout,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": str(exc.stdout or "")[-_MAX_OUTPUT_CHARS:],
            "stderr": str(exc.stderr or "")[-_MAX_OUTPUT_CHARS:],
        }
    except OSError as exc:
        return {
            "ok": False,
            "status": "error",
            "error": "test_runner_unavailable",
            "details": str(exc)[:500],
        }
