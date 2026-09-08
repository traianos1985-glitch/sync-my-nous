context = {
    "memory": {},
    "plugins": {},
    "state": "running"
}

def get_context():
    return context

def update_context(key, value):
    context[key] = value
    return context
