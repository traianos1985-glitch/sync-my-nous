import sys
import json
from executor.document_chat_bridge import document_chat_answer, format_document_answer

q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
if not q:
    print(json.dumps({"ok": False, "error": "missing_question"}, indent=2, ensure_ascii=False))
else:
    print(json.dumps(document_chat_answer(q), indent=2, ensure_ascii=False))
    print("\n--- formatted ---\n")
    print(format_document_answer(q))
