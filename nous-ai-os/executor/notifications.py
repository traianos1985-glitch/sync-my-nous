import subprocess

def notify(title, message):

    try:
        subprocess.run([
            "termux-notification",
            "--title", str(title),
            "--content", str(message)
        ])
        return True

    except Exception as e:
        return str(e)
