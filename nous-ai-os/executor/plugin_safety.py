import shutil
import os

def quarantine_plugin(path):

    try:
        os.makedirs("executor/quarantine", exist_ok=True)

        filename = path.split("/")[-1]
        shutil.move(path, f"executor/quarantine/{filename}")

        return {
            "status": "quarantined",
            "file": filename
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
