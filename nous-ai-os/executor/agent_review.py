from executor.memory import load


def review_last():
    mem = load()[-10:]

    commands = []
    events = []

    for item in mem:
        if isinstance(item, dict):
            if item.get("command"):
                commands.append(item.get("command"))
            if item.get("event"):
                events.append(item.get("event"))

    last_command = commands[-1] if commands else "δεν βρέθηκε πρόσφατη εντολή"
    last_event = events[-1] if events else "δεν βρέθηκε πρόσφατο γεγονός"

    return (
        "Έλεγχος τελευταίων ενεργειών\n\n"
        "1. Τι έγινε:\n"
        f"- Τελευταία εντολή: {last_command}\n"
        f"- Τελευταίο γεγονός: {last_event}\n\n"
        "2. Αν πέτυχε:\n"
        "- Το σύστημα συνεχίζει να λειτουργεί και η μνήμη ενημερώνεται.\n\n"
        "3. Πρόβλημα ή ρίσκο:\n"
        "- Το βασικό ρίσκο είναι να γίνονται πολλές αλλαγές μαζί χωρίς compile και Git checkpoint.\n\n"
        "4. Επόμενο μικρό βήμα:\n"
        "- Συνέχισε με μικρές αναβαθμίσεις, py_compile, commit και push πριν από restart ή νέο μεγάλο βήμα."
    )
