---
name: ask_with_turns return type
description: executor/remote_llm.py ask_with_turns() returns a dict, not a plain string
---

`ask_with_turns(turns, system)` in `executor/remote_llm.py` returns:
  `{"success": True, "model": "...", "response": "...text..."}` on success
  `{"success": False, "error": "..."}` on failure

**Why:** The function signature says `-> dict` but callers often expect a string.

**How to apply:** Always do:
```python
result = ask_with_turns(turns, system=system)
text = result.get("response") or result.get("error") or str(result)
```
Same applies to `ask_remote_llm()`.
