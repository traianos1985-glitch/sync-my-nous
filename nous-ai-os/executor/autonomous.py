import difflib
import time
from executor.core import safe_execute_patch, MEMORY, ask_approval


def generate_diff(old, new):
    return "\n".join(
        difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            lineterm=""
        )
    )


def apply_if_safe(file, new_content):
    try:
        with open(file, "r", encoding="utf-8") as f:
            old_content = f.read()
    except:
        old_content = ""

    diff = generate_diff(old_content, new_content)

    print("\n[DIFF PREVIEW]")
    print(diff if diff else "[no changes]")

    MEMORY.remember({
        "event": "diff_generated",
        "file": file,
        "diff": diff
    })

    if not ask_approval(f"Apply diff to {file}?"):
        print("[ABORTED]")
        return False

    return safe_execute_patch(file, new_content)
