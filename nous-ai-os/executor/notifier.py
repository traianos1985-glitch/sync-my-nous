import subprocess

def notify(title, message):
    try:
        subprocess.run([
            "termux-notification",
            "--title", title,
            "--content", str(message)
        ])
    except Exception as e:
        print("[NOTIFY ERROR]", e)
