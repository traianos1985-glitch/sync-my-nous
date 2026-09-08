from executor.snapshots import create_snapshot

def safe_execute(action_fn, *args, **kwargs):

    # 1. always snapshot πριν αλλαγές
    snap = create_snapshot()

    try:
        result = action_fn(*args, **kwargs)
        return {
            "success": True,
            "snapshot": snap,
            "result": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "rolled_back_snapshot": snap
        }
