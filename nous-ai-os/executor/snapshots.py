import shutil
import os
from datetime import datetime

SNAP_DIR = "executor/snapshots"
os.makedirs(SNAP_DIR, exist_ok=True)

def create_snapshot():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_path = os.path.join(SNAP_DIR, ts)
    shutil.copytree("executor", snap_path, ignore=shutil.ignore_patterns("snapshots"))
    return {"snapshot_created": snap_path}

def list_snapshots():
    return os.listdir(SNAP_DIR)

def rollback(snapshot_name):
    src = os.path.join(SNAP_DIR, snapshot_name)
    if not os.path.exists(src):
        return {"error": "snapshot not found"}

    shutil.rmtree("executor")
    shutil.copytree(src, "executor")
    return {"rolled_back_to": snapshot_name}
