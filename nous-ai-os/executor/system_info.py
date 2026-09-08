import os
import platform
import time

def info():
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cwd": os.getcwd(),
        "time": time.time(),
        "system": "NOUS AI OS"
    }
