from executor.file_ops import backup_file
from executor.validator import validate_python
from executor.rollback import rollback
import os

def patch_file(path, new_content):
    print("[PATCH] Starting...")

    backup = backup_file(path)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print("[PATCH] Written")

        if path.endswith(".py"):
            ok = validate_python(path)
        else:
            ok = True

        if not ok:
            print("[PATCH] INVALID -> rollback")
            rollback(backup, path)
            return False

        print("[PATCH] SUCCESS")
        return True

    except Exception as e:
        print("[PATCH ERROR]", e)
        rollback(backup, path)
        return False


if __name__ == "__main__":
    print("PATCH ENGINE READY")
