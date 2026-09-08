import py_compile
import os

FILES = [
    "executor/router.py",
    "executor/kernel.py",
    "executor/intent.py",
    "executor/tools.py",
    "executor/llm_core.py",
    "executor/brain.py",
    "executor/hybrid_agent.py",
    "executor/control_center.py",
]

def check():
    results = {}

    for f in FILES:
        try:
            py_compile.compile(f, doraise=True)
            results[f] = "ok"
        except Exception as e:
            results[f] = str(e)

    return results
