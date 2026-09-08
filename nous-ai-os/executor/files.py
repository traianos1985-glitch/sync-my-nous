import os

UPLOAD_DIR = "executor/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_file(filename, content):
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)
    return {"saved": filename, "path": path}

def read_file(path):
    with open(path, "rb") as f:
        return f.read()
