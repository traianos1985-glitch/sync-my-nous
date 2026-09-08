import sys, json
from executor.conversation_manager import (
    new_conversation,
    list_conversations,
    get_conversation,
    append_turn,
    rename_conversation,
    delete_conversation,
    conversation_context,
)

cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

if cmd == "new":
    title = " ".join(sys.argv[2:]) or "Νέα συνομιλία"
    print(json.dumps(new_conversation(title), indent=2, ensure_ascii=False))
elif cmd == "list":
    print(json.dumps(list_conversations(), indent=2, ensure_ascii=False))
elif cmd == "get":
    print(json.dumps(get_conversation(sys.argv[2]), indent=2, ensure_ascii=False))
elif cmd == "append":
    cid = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None
    user = sys.argv[3] if len(sys.argv) > 3 else "test user"
    ans = sys.argv[4] if len(sys.argv) > 4 else "test answer"
    print(json.dumps(append_turn(user, ans, conversation_id=cid), indent=2, ensure_ascii=False))
elif cmd == "context":
    print(conversation_context(sys.argv[2]))
elif cmd == "rename":
    print(json.dumps(rename_conversation(sys.argv[2], " ".join(sys.argv[3:])), indent=2, ensure_ascii=False))
elif cmd == "delete":
    print(json.dumps(delete_conversation(sys.argv[2]), indent=2, ensure_ascii=False))
else:
    print(json.dumps({"ok": False, "error": "unknown_command"}, indent=2, ensure_ascii=False))
