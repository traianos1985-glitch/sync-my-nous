import shutil
import os
import time

def backup_router():

    src="executor/router.py"

    if not os.path.exists(src):
        return False

    dst=f"backups/router_{int(time.time())}.py"

    shutil.copy(src,dst)

    return dst

def latest_backup():

    if not os.path.exists("backups"):
        return None

    files=[
        os.path.join("backups",x)
        for x in os.listdir("backups")
    ]

    if not files:
        return None

    files.sort()

    return files[-1]

def restore_latest():

    latest=latest_backup()

    if not latest:
        return False

    shutil.copy(latest,"executor/router.py")

    return True
