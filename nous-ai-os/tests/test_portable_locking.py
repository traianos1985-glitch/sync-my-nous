"""Cross-platform file locking (executor.portable_fcntl).

The Windows branch is exercised with a faithful *fake* ``msvcrt`` because the CI and
development hosts are POSIX. This verifies the emulation logic and that NOUS state
modules import and work without ``fcntl``; it does not replace a run on real Windows.
"""
import ast
import importlib.util
import os
import subprocess
import sys
import textwrap
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "executor"

FAKE_MSVCRT = textwrap.dedent('''
    """Fake msvcrt: byte-range lock semantics reduced to one lock per file (by inode)."""
    import errno, os, threading
    LK_UNLCK, LK_LOCK, LK_NBLCK, LK_RLCK, LK_NBRLCK = 0, 1, 2, 3, 4
    _held = {}
    _guard = threading.Lock()

    def locking(fd, mode, nbytes):
        key = os.fstat(fd).st_ino
        with _guard:
            if mode == LK_UNLCK:
                if _held.get(key) != fd:
                    raise OSError(errno.EACCES, "not locked by this handle")
                del _held[key]
                return
            if key in _held and _held[key] != fd:
                raise OSError(errno.EACCES, "locked by another handle")
            _held[key] = fd
''')


def _load_portable(name, monkeypatch, tmp_path, windows):
    """Import a fresh copy of portable_fcntl, optionally pretending to be Windows."""
    if windows:
        fake = tmp_path / "fake_msvcrt.py"
        fake.write_text(FAKE_MSVCRT, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("msvcrt", fake)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        monkeypatch.setitem(sys.modules, "msvcrt", module)
        monkeypatch.setitem(sys.modules, "fcntl", None)  # `import fcntl` -> ImportError
    spec = importlib.util.spec_from_file_location(name, EXECUTOR / "portable_fcntl.py")
    portable = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(portable)
    return portable


def test_posix_backend_is_transparent_passthrough(tmp_path):
    import fcntl as real
    from executor import portable_fcntl as portable
    if os.name != "posix":
        pytest.skip("POSIX only")
    assert portable.BACKEND == "fcntl"
    assert (portable.LOCK_EX, portable.LOCK_UN, portable.LOCK_NB) == (real.LOCK_EX, real.LOCK_UN, real.LOCK_NB)
    first = open(tmp_path / "l", "a")
    second = open(tmp_path / "l", "a")
    try:
        portable.flock(first.fileno(), portable.LOCK_EX)
        with pytest.raises(BlockingIOError):
            portable.flock(second.fileno(), portable.LOCK_EX | portable.LOCK_NB)
        portable.flock(first.fileno(), portable.LOCK_UN)
        portable.flock(second.fileno(), portable.LOCK_EX | portable.LOCK_NB)
    finally:
        first.close()
        second.close()


def test_windows_emulation_nonblocking_conflict_and_release(monkeypatch, tmp_path):
    portable = _load_portable("pf_win_a", monkeypatch, tmp_path, windows=True)
    assert portable.BACKEND == "msvcrt"
    a = open(tmp_path / "lock", "a")
    b = open(tmp_path / "lock", "a")
    try:
        portable.flock(a.fileno(), portable.LOCK_EX)
        with pytest.raises(BlockingIOError):
            portable.flock(b.fileno(), portable.LOCK_EX | portable.LOCK_NB)
        portable.flock(a.fileno(), portable.LOCK_UN)
        portable.flock(b.fileno(), portable.LOCK_EX | portable.LOCK_NB)
        portable.flock(b.fileno(), portable.LOCK_UN)
    finally:
        a.close()
        b.close()


def test_windows_emulation_unlock_of_unlocked_file_is_noop(monkeypatch, tmp_path):
    portable = _load_portable("pf_win_b", monkeypatch, tmp_path, windows=True)
    with open(tmp_path / "lock", "a") as handle:
        portable.flock(handle.fileno(), portable.LOCK_UN)  # must not raise


def test_windows_emulation_blocking_lock_waits_for_release(monkeypatch, tmp_path):
    portable = _load_portable("pf_win_c", monkeypatch, tmp_path, windows=True)
    holder = open(tmp_path / "lock", "a")
    waiter = open(tmp_path / "lock", "a")
    acquired = threading.Event()
    portable.flock(holder.fileno(), portable.LOCK_EX)

    def wait_for_lock():
        portable.flock(waiter.fileno(), portable.LOCK_EX)
        acquired.set()

    thread = threading.Thread(target=wait_for_lock, daemon=True)
    thread.start()
    try:
        time.sleep(0.2)
        assert not acquired.is_set(), "blocking flock must not succeed while the lock is held"
        portable.flock(holder.fileno(), portable.LOCK_UN)
        assert acquired.wait(3), "blocking flock must proceed once the lock is released"
        portable.flock(waiter.fileno(), portable.LOCK_UN)
    finally:
        thread.join(3)
        holder.close()
        waiter.close()


def test_windows_emulation_preserves_file_position(monkeypatch, tmp_path):
    portable = _load_portable("pf_win_d", monkeypatch, tmp_path, windows=True)
    path = tmp_path / "data"
    path.write_text("0123456789", encoding="utf-8")
    with open(path, "r+b") as handle:
        handle.seek(4)
        portable.flock(handle.fileno(), portable.LOCK_EX)
        assert os.lseek(handle.fileno(), 0, os.SEEK_CUR) == 4
        portable.flock(handle.fileno(), portable.LOCK_UN)
        assert os.lseek(handle.fileno(), 0, os.SEEK_CUR) == 4


def test_no_executor_module_imports_fcntl_directly():
    offenders = []
    for path in sorted(EXECUTOR.rglob("*.py")):
        if path.name == "portable_fcntl.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:  # top-level statements only
            if isinstance(node, ast.Import) and any(alias.name == "fcntl" for alias in node.names):
                offenders.append(str(path.relative_to(ROOT)))
            if isinstance(node, ast.ImportFrom) and node.module == "fcntl":
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"use executor.portable_fcntl instead of fcntl: {offenders}"


def _run_without_fcntl(tmp_path, code):
    """Run code in a fresh interpreter that sees no fcntl but has the fake msvcrt.

    The fake is injected into sys.modules only after stdlib modules that sniff for
    ``msvcrt`` (subprocess, getpass, ...) are imported, so they keep their POSIX paths.
    """
    (tmp_path / "fake_msvcrt.py").write_text(FAKE_MSVCRT, encoding="utf-8")
    bootstrap = textwrap.dedent(f"""
        import sys, importlib.util
        import subprocess, getpass, tempfile, shutil, threading, asyncio, multiprocessing
        spec = importlib.util.spec_from_file_location("msvcrt", r"{tmp_path / 'fake_msvcrt.py'}")
        fake = importlib.util.module_from_spec(spec); spec.loader.exec_module(fake)
        sys.modules["msvcrt"] = fake
        sys.modules["fcntl"] = None
    """) + textwrap.dedent(code)
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-c", bootstrap], cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=120)


def test_lock_protected_state_modules_import_without_fcntl(tmp_path):
    result = _run_without_fcntl(tmp_path, """
        import executor.api_tokens, executor.operator_approval, executor.json_state_store
        import executor.json_object_store, executor.task_queue, executor.action_log
        import executor.agent_journal, executor.autonomy_service, executor.runtime_metrics
        import executor.auto_mission_executor
        from executor import portable_fcntl
        print(portable_fcntl.BACKEND)
    """)
    assert result.returncode == 0, result.stderr[-800:]
    assert result.stdout.strip().endswith("msvcrt")


def test_full_backend_app_imports_without_fcntl(tmp_path):
    result = _run_without_fcntl(tmp_path, """
        import executor.router as router
        print(len(list(router.app.url_map.iter_rules())) > 100)
    """)
    assert result.returncode == 0, result.stderr[-800:]
    assert result.stdout.strip().endswith("True")


def test_approval_queue_round_trips_on_emulated_backend(tmp_path):
    result = _run_without_fcntl(tmp_path, """
        from executor import operator_approval as oa
        item = oa.request_approval("test_action", {"command": "x"}, reason="portability check")
        pending = [i for i in oa.list_approvals(status="pending") if i.get("id") == item.get("id")]
        print("pending", len(pending))
    """)
    assert result.returncode == 0, result.stderr[-800:]
