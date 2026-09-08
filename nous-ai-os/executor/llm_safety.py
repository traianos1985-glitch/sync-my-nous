import json

def validate(llm_output):

    try:
        if isinstance(llm_output, str):
            data = json.loads(llm_output)
        else:
            data = llm_output

        allowed_keys = ["intent", "action", "code"]

        return {k: data.get(k, None) for k in allowed_keys}

    except:
        return {
            "intent": "invalid",
            "action": "none",
            "code": None
        }
