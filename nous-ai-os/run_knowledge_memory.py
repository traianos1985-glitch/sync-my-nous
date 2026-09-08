import sys, json
from executor.knowledge_memory_engine import (
    status, search_knowledge, answer_from_knowledge_memory,
    remember_knowledge, search_code_lessons, coding_context
)

cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

if cmd == "status":
    print(json.dumps(status(), indent=2, ensure_ascii=False))
elif cmd == "search":
    print(json.dumps(search_knowledge(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
elif cmd == "answer":
    print(json.dumps(answer_from_knowledge_memory(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
elif cmd == "remember":
    q = sys.argv[2] if len(sys.argv) > 2 else ""
    a = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
    print(json.dumps(remember_knowledge(q, a), indent=2, ensure_ascii=False))
elif cmd == "code":
    print(coding_context(" ".join(sys.argv[2:])))
elif cmd == "code-search":
    print(json.dumps(search_code_lessons(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
else:
    print(json.dumps({"ok": False, "error": "unknown_command"}, indent=2, ensure_ascii=False))
