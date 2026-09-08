from executor.compile_check import check
from executor.health import backup

def stable_point():
    result = check()
    ok = all(v == "ok" for v in result.values())
    if ok:
        b = backup()
        return {"compile": result, "backup": b, "stable": True}
    return {"compile": result, "stable": False}
