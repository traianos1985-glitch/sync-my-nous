import json
from executor.chat_capabilities import chat_capabilities
print(json.dumps(chat_capabilities(), indent=2, ensure_ascii=False))
