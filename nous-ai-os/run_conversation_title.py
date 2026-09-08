import sys, json
from executor.conversation_title_engine import generate_conversation_title, auto_title_recent_conversations

if len(sys.argv) > 1:
    print(json.dumps(generate_conversation_title(sys.argv[1]), indent=2, ensure_ascii=False))
else:
    print(json.dumps(auto_title_recent_conversations(), indent=2, ensure_ascii=False))
