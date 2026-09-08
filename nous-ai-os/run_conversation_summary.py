import sys, json
from executor.conversation_summary_engine import update_conversation_summary

cid = sys.argv[1] if len(sys.argv) > 1 else ""
print(json.dumps(update_conversation_summary(cid), indent=2, ensure_ascii=False))
