import sys, json
from executor.chat_brain_v3 import answer_chat

q = " ".join(sys.argv[1:]) or "Τι κάνεις;"
print(json.dumps(answer_chat(q), indent=2, ensure_ascii=False))
