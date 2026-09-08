def ask_approval(action):

    print(f"[APPROVAL REQUIRED] {action}")

    ans = input("Approve? (y/n): ").strip().lower()

    return ans == "y"
