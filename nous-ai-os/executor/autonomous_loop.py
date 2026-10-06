import time

from executor import autonomy
from executor.autonomy_v3 import autonomy_cycle
from executor.battery_guard import battery_guard


def battery_allows_run(min_level=25):
    info = battery_guard()
    level = info.get("level")
    plugged = str(info.get("plugged", "")).upper()

    if isinstance(level, (int, float)) and level < int(min_level) and plugged == "UNPLUGGED":
        return False, info

    return True, info


def run_once(min_battery=25):
    allowed, battery = battery_allows_run(min_battery)

    if not allowed:
        result = {
            "skipped": True,
            "reason": "low_battery",
            "battery": battery,
        }
        return autonomy.mark_run(result)

    result = autonomy_cycle()
    return autonomy.mark_run(result)


def run(goal="keep alive", interval=300, max_cycles=None):
    """
    Safe autonomy loop.

    interval:
        seconds between cycles. Default 300 = 5 minutes.

    max_cycles:
        None = run until stopped
        number = stop after that many cycles, useful for tests
    """
    autonomy.start()

    cycles = 0
    failures = 0

    while autonomy.status().get("running"):
        started = time.time()
        try:
            result = run_once()
            failures = 0
            print("[AUTONOMY LOOP]", result, f"({time.time() - started:.2f}s)")
        except Exception as exc:  # never let one bad cycle kill the loop
            failures += 1
            print(f"[AUTONOMY LOOP] cycle failed ({failures} in a row): {exc!r}")

        cycles += 1
        if max_cycles is not None and cycles >= int(max_cycles):
            autonomy.stop()
            break

        # exponential backoff on repeated failures, capped at 1 hour
        delay = interval if failures == 0 else min(interval * (2 ** min(failures, 4)), 3600)
        time.sleep(delay)

    return {
        "stopped": True,
        "cycles": cycles,
        "status": autonomy.status(),
    }


if __name__ == "__main__":
    import sys

    interval = 300

    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            interval = 300

    print(f"Starting NOUS autonomy loop every {interval} seconds.")
    print("Press CTRL+C to stop.")

    try:
        run(interval=interval)
    except KeyboardInterrupt:
        autonomy.stop()
        print("\nAutonomy loop stopped.")
