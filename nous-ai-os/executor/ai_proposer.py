import os
from executor.patch_engine import patch_file

def propose_change(path, transformer_func):
    print("[AI] Reading file...")

    with open(path, "r", encoding="utf-8") as f:
        old = f.read()

    print("[AI] Generating proposal...")
    new = transformer_func(old)

    print("\n--- PROPOSED CHANGE ---\n")
    print(new)
    print("\n-----------------------\n")

    ans = input("Apply change? (yes/no): ")

    if ans.lower() == "yes":
        return patch_file(path, new)
    else:
        print("[AI] Cancelled")
        return False


if __name__ == "__main__":
    print("AI PROPOSER READY")
