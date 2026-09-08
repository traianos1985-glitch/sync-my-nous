import time
from executor.self_improver import improve

def run_loop(interval=10):

    while True:
        result = improve()

        print("[LOOP]", result)

        time.sleep(interval)
