import time

from executor import autonomy
from executor.autonomy_v3 import autonomy_cycle
from executor.battery_guard import battery_guard


def battery_allows_run(min_level=25):
    info = battery_guard()
    level = int(info.get("level", 100))
    plugged = str(info.get("plugged", "")).upper()

    if level < int(min_level) and plugged == "UNPLUGGED":
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

    while autonomy.status().get("running"):
        result = run_once()
        print("[AUTONOMY LOOP]", result)

        cycles += 1
        if max_cycles is not None and cycles >= int(max_cycles):
            autonomy.stop()
            break

        time.sleep(interval)

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
