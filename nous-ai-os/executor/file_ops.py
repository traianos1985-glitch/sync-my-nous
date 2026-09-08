import os
import shutil
import time

BACKUP_DIR = "_backup"

def timestamp():
    return time.strftime("%Y%m%d_%H%M%S")

def backup_file(path):
    if not os.path.exists(path):
        return None

    folder = os.path.join(BACKUP_DIR, timestamp())
    os.makedirs(folder, exist_ok=True)

    dst = os.path.join(folder, os.path.basename(path))
    shutil.copy2(path, dst)

    return dst

def safe_write(path, content):
    backup = backup_file(path)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return backup

def restore_backup(backup_path, original_path):
    shutil.copy2(backup_path, original_path)

if __name__ == "__main__":
    print("FILE OPS READY")
