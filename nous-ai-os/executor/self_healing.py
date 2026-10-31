import os
import subprocess
import sys


def restart_server():
    """Restart the router without invoking a shell or inheriting stdin."""
    subprocess.Popen(
        [sys.executable, "executor/router.py"],
        cwd=os.getcwd(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=(os.name == "posix"),
    )
    return True
