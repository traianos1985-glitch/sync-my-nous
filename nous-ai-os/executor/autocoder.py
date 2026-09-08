from executor.llm_core import ask

def generate(task, error=None):

    prompt = f"""
You are a Python plugin generator.

Task:
{task}

"""

    if error:
        prompt += f"\nFix this error:\n{error}\n"

    prompt += """
Return ONLY valid Python code.
Must include function: run()
"""

    return ask(prompt)
