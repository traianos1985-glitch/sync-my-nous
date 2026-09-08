
def parse_command(text):

    parts = text.split()

    return {
        "command": parts[0],
        "args": parts[1:]
    }
