import os
import base64

UPLOAD_DIR = "uploads"

def save_image(file):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(path)
    return {
        "saved": True,
        "path": path,
        "type": "image"
    }

def image_preview(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return {
        "path": path,
        "base64_preview": b64[:1500]
    }
