import os

def snapshot():

    files = []

    for root, dirs, names in os.walk("executor"):
        if "__pycache__" in root:
            continue

        for n in names:
            if n.endswith(".py"):
                files.append(os.path.join(root, n))

    return {
        "python_files": files,
        "count": len(files)
    }
