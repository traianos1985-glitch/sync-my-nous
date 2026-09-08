import importlib
from executor.safe_libs import is_allowed

def safe_import(module):
    if not is_allowed(module):
        return {"error": "blocked module"}

    return importlib.import_module(module)
