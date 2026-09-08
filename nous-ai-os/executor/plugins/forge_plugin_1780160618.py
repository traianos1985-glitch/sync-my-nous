import datetime

def run():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"time": now}