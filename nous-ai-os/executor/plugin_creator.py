import os

def create_plugin(name, code):
    path = f"executor/plugins/{name}.py"
    with open(path, "w") as f:
        f.write(code)
    return {"created": name, "path": path}
