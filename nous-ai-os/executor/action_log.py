import json, os, time

FILE="data/action_log.json"

def log_action(action, result=None):
    os.makedirs("data", exist_ok=True)
    try:
        data=json.load(open(FILE,"r",encoding="utf-8"))
    except:
        data=[]
    item={"time":time.time(),"action":action,"result":result}
    data.append(item)
    json.dump(data[-300:],open(FILE,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    return item

def recent_actions():
    try:
        return json.load(open(FILE,"r",encoding="utf-8"))[-20:]
    except:
        return []
