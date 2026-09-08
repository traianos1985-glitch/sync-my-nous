from executor.autocoder import generate
from executor.code_tester import test_plugin
from executor.plugin_creator import create_plugin
from executor.snapshots import create_snapshot, rollback
import time

def run(task, max_cycles=5):

    snapshot = create_snapshot()

    code = None
    error = None

    for i in range(max_cycles):

        print(f"[CYCLE {i}] generating code")

        code = generate(task, error)

        result = test_plugin(code)

        if result["success"]:
            plugin_name = f"auto_{int(time.time())}"
            return create_plugin(plugin_name, code)

        error = result["error"]

        print("[FIXING ERROR]", error)

    # rollback if failed
    return rollback(snapshot["snapshot_created"])
