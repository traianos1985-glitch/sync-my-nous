from executor.safe_core import safe_execute
from executor.router import execute as real_execute

def execute(command, context=None):
    return safe_execute(real_execute, command)
