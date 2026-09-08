from executor.approval import ask_approval
from executor.patch_engine import patch_file

def secure_patch(file, content):

    approved = ask_approval(f"Patch file: {file}")

    if not approved:
        print("[PATCH BLOCKED]")
        return False

    return patch_file(file, str(content))
