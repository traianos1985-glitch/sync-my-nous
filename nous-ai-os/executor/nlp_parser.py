def normalize(text):

    return text.strip().lower()


def parse_natural_command(command):

    cmd = normalize(command)

    # STATUS

    if (
        "κατάσταση αυτόνομης λειτουργίας" in cmd
        or "autonomous status" in cmd
    ):

        return "/autonomous-status"

    if (
        "ποια είναι η κατάσταση του συστήματος" in cmd
        or "κατάσταση συστήματος" in cmd
        or "status" == cmd
        or "κατάσταση" == cmd
    ):

        return "/status"

    # MEMORY

    if "μνήμη" in cmd:

        return "/memory"

    # AUTONOMOUS EVOLUTION

    if (
        "αυτόνομη εξέλιξη" in cmd
        or "autonomous evolve" in cmd
    ):

        return "/autonomous-evolve"

    if (
        "ξεκίνα αυτόνομη λειτουργία" in cmd
    ):

        return "/autonomous-start"

    if (
        "σταμάτα αυτόνομη λειτουργία" in cmd
    ):

        return "/autonomous-stop"

    # NORMAL EVOLUTION

    if (
        "κάνε εξέλιξη" in cmd
        or "evolve" == cmd
        or "εξέλιξη" == cmd
    ):

        return "/evolve"

    # REAL EVOLUTION

    if "γράψε plugin" in cmd:

        goal = command.replace(
            "γράψε plugin",
            ""
        ).strip()

        return f"/real-evolve {goal}"

    if "φτιάξε plugin" in cmd:

        goal = command.replace(
            "φτιάξε plugin",
            ""
        ).strip()

        return f"/real-evolve {goal}"

    if "create plugin" in cmd:

        goal = command.replace(
            "create plugin",
            ""
        ).strip()

        return f"/real-evolve {goal}"

    # SEARCH

    if cmd.startswith("ψάξε "):

        query = command.split(" ", 1)[1]

        return f"/search {query}"

    if cmd.startswith("search "):

        query = command.split(" ", 1)[1]

        return f"/search {query}"

    return command
