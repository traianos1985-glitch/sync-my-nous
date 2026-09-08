def ensure_output(result):

    if result is None:
        return "⚠️ EMPTY RESPONSE"

    if isinstance(result, dict):

        # priority extraction
        for key in ["output", "response", "llm", "result"]:
            if key in result:
                val = result[key]

                if isinstance(val, dict) and "response" in val:
                    return val["response"]

                return str(val)

        return str(result)

    return str(result)
