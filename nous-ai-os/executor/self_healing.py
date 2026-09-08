
import subprocess
import time

def restart_server():

    subprocess.Popen(
        ["python", "executor/router.py"]
    )

    return True
