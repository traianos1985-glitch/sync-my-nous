import subprocess, time

def run(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=30)
    except Exception as e:
        return str(e)

def git_status():
    return run(["git", "status", "--short"])

def git_checkpoint(message="NOUS auto checkpoint"):
    run(["git", "add", "."])
    commit = run(["git", "commit", "-m", message])
    push = run(["git", "push"])
    return {"commit": commit, "push": push}
