"""Portable stand-in for the small ``fcntl.flock`` subset used by NOUS state stores.

On POSIX this is a transparent pass-through to :mod:`fcntl`; behaviour is unchanged.
On Windows (where ``fcntl`` does not exist) it emulates the same calls with
``msvcrt.locking`` so token storage, the approval queue, mission state and the other
lock-protected stores can be imported and used instead of failing at start-up.

Semantics kept identical for callers:
* ``flock(fd, LOCK_EX)``            blocks until the lock is obtained.
* ``flock(fd, LOCK_EX | LOCK_NB)``  raises ``BlockingIOError`` when already locked.
* ``flock(fd, LOCK_UN)``            releases; unlocking an unlocked file is a no-op.

Limitation (documented, intentional): ``LOCK_SH`` is treated as exclusive on Windows.
No caller in NOUS uses shared locks.
"""
from __future__ import annotations

import errno
import os
import time

try:  # POSIX
    import fcntl as _fcntl
except ImportError:  # Windows and other platforms without fcntl
    _fcntl = None

LOCK_SH = 1
LOCK_EX = 2
LOCK_NB = 4
LOCK_UN = 8

_POLL_SECONDS = 0.05

if _fcntl is not None:
    LOCK_SH = _fcntl.LOCK_SH
    LOCK_EX = _fcntl.LOCK_EX
    LOCK_NB = _fcntl.LOCK_NB
    LOCK_UN = _fcntl.LOCK_UN

    def flock(fd, operation):
        return _fcntl.flock(fd, operation)

    BACKEND = "fcntl"
else:
    import msvcrt  # type: ignore[import-not-found]

    def _try_lock(fd) -> None:
        position = os.lseek(fd, 0, os.SEEK_CUR)
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        finally:
            os.lseek(fd, position, os.SEEK_SET)

    def _unlock(fd) -> None:
        position = os.lseek(fd, 0, os.SEEK_CUR)
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass  # flock(LOCK_UN) on an unlocked file is a no-op
        finally:
            os.lseek(fd, position, os.SEEK_SET)

    def flock(fd, operation):
        if operation & LOCK_UN:
            _unlock(fd)
            return None
        nonblocking = bool(operation & LOCK_NB)
        while True:
            try:
                _try_lock(fd)
                return None
            except OSError as exc:
                if nonblocking:
                    raise BlockingIOError(errno.EAGAIN, "resource temporarily unavailable") from exc
                time.sleep(_POLL_SECONDS)

    BACKEND = "msvcrt"

__all__ = ["flock", "LOCK_SH", "LOCK_EX", "LOCK_NB", "LOCK_UN", "BACKEND"]
