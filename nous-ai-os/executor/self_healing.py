
import subprocess

def restart_server():

    subprocess.Popen(
        ["python", "executor/router.py"]
    )

    return True
