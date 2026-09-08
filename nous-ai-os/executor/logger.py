from datetime import datetime

def log(event, data=None):
    line = f"[{datetime.now()}] {event} {data}\n"
    with open("executor/logs.txt", "a") as f:
        f.write(line)
