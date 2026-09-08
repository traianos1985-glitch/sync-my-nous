import os

ALLOWED_PREFIX="executor/"

def read_source(path):
    path=str(path).strip()
    if not path.startswith(ALLOWED_PREFIX):
        return {"error":"blocked_path"}
    if not os.path.exists(path):
        return {"error":"not_found"}
    if not path.endswith(".py"):
        return {"error":"only_py_allowed"}
    return {"path":path,"content":open(path,"r",encoding="utf-8").read()[:6000]}
