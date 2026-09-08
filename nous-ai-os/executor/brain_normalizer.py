def normalize(response, command):

    # αν έρχεται dict από fallback LLM
    if isinstance(response, dict):

        if "llm" in response:
            return response["llm"].get("response", "NO_OUTPUT")

        if "response" in response:
            return response["response"]

    # string fallback
    return str(response)
