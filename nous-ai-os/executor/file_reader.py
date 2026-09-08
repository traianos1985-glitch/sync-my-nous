import os

UPLOAD_DIR = "uploads"

def save_upload(file):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(path)
    return {"saved": True, "path": path}

def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:5000]
    except Exception as e:
        return str(e)
