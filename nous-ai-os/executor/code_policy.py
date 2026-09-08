RULES = {
    "must_have_run_function": True,
    "no_import_pip": True,
    "max_file_size_kb": 50,
    "no_os_system_calls": False
}

def validate(code: str):
    if "pip" in code:
        return False, "pip blocked"

    if "os.system" in code:
        return False, "os.system discouraged"

    return True, "ok"
