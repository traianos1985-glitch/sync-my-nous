import sys, json
from executor.error_learning_engine import (
    status, search_errors, search_solutions,
    remember_error, remember_solution, engineering_memory_context,
)

cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

if cmd == "status":
    print(json.dumps(status(), indent=2, ensure_ascii=False))
elif cmd == "search-errors":
    print(json.dumps(search_errors(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
elif cmd == "search-solutions":
    print(json.dumps(search_solutions(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
elif cmd == "context":
    print(engineering_memory_context(" ".join(sys.argv[2:])))
elif cmd == "remember-error":
    print(json.dumps(remember_error(sys.argv[2], " ".join(sys.argv[3:])), indent=2, ensure_ascii=False))
elif cmd == "remember-solution":
    print(json.dumps(remember_solution(sys.argv[2], " ".join(sys.argv[3:])), indent=2, ensure_ascii=False))
else:
    print(json.dumps({"ok": False, "error": "unknown_command"}, indent=2, ensure_ascii=False))
