history = []

def add(cmd):
    history.append(cmd)

def get_all():
    return history[-50:]
