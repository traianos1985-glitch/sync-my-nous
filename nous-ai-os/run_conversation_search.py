import sys, json
from executor.conversation_search_engine import answer_from_conversations

q = " ".join(sys.argv[1:])
print(json.dumps(answer_from_conversations(q), indent=2, ensure_ascii=False))
