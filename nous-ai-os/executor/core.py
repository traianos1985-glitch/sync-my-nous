import os
import time
import shutil
from datetime import datetime

# =========================
# MEMORY LAYER
# =========================
class Memory:
    def __init__(self):
        self.data = []

    def remember(self, item):
        self.data.append({
            "time": time.time(),
            "item": item
        })

MEMORY = Memory()


# =========================
# APPROVAL LAYER
# =========================
def ask_approval(action):
    print(f"\n[APPROVAL REQUIRED] {action}")
    ans = input("Approve? (y/n): ").strip().lower()
    return ans == "y"


# =========================
# BACKUP / RECOVERY LAYER
# =========================
def backup_file(path):
    if not os.path.exists(path):
        return None

    backup_dir = "_backup"
    os.makedirs(backup_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_dir}/{os.path.basename(path)}.{ts}.bak"

    shutil.copy2(path, backup_path)
    return backup_path


def restore_latest(path):
    backup_dir = "_backup"
    if not os.path.exists(backup_dir):
        return False

    files = [f for f in os.listdir(backup_dir) if f.startswith(os.path.basename(path))]
    if not files:
        return False

    latest = sorted(files)[-1]
    shutil.copy2(f"{backup_dir}/{latest}", path)
    return True


# =========================
# VALIDATION LAYER
# =========================
def validate_python(code):
    try:
        compile(code, "<string>", "exec")
        return True
    except Exception as e:
        print("[VALIDATION ERROR]", e)
        return False


# =========================
# PATCH ENGINE
# =========================
def patch_file(path, new_content):
    MEMORY.remember({"event": "patch_start", "file": path})

    # backup
    backup = backup_file(path)

    # validation
    if path.endswith(".py"):
        if not validate_python(new_content):
            print("[ABORT] Invalid Python code")
            return False

    # approval
    if not ask_approval(f"Write to {path}"):
        print("[CANCELLED]")
        return False

    # write
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        print("[WRITE ERROR]", e)
        if backup:
            restore_latest(path)
        return False

    MEMORY.remember({"event": "patch_done", "file": path})
    print("[OK] Patch applied")

    return True


# =========================
# AUTO RECOVERY WRAPPER
# =========================
def safe_execute_patch(path, content):
    try:
        return patch_file(path, content)
    except Exception as e:
        print("[CRASH DETECTED]", e)
        restore_latest(path)
        return False
