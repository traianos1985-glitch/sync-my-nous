def generate_plugin(name, logic):
    # SAFE TEMPLATE ONLY (no arbitrary execution)
    return f"""
def run():
    {logic}
    return "{name} executed"
"""
