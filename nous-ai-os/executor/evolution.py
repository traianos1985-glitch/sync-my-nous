import time
import os
from executor.core import safe_execute_patch, MEMORY

WATCH_FILES = [
    "demo.py",
    "demo.html"
]

def scan_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return None


def suggest_improvements(content, path):
    suggestions = []

    if path.endswith(".py"):
        if "print(" in content and "log" not in content:
            suggestions.append("Add logging system instead of print")

        if "except:" in content:
            suggestions.append("Use specific exception handling")

    if path.endswith(".html"):
        if "<button" in content and "class=" not in content:
            suggestions.append("Add CSS classes for UI consistency")

    return suggestions


def evolve_loop(interval=5):
    print("[EVOLUTION ENGINE STARTED]")

    last_state = {}

    while True:
        for file in WATCH_FILES:
            content = scan_file(file)
            if content is None:
                continue

            if file not in last_state or last_state[file] != content:
                print(f"\n[CHANGE DETECTED] {file}")

                suggestions = suggest_improvements(content, file)

                if suggestions:
                    print("[SUGGESTIONS]")
                    for s in suggestions:
                        print("-", s)

                    MEMORY.remember({
                        "event": "suggestions",
                        "file": file,
                        "suggestions": suggestions
                    })

                last_state[file] = content

        time.sleep(interval)
