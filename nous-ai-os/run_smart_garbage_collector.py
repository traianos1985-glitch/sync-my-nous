from executor.smart_garbage_collector import run_smart_garbage_collector
import json

print(json.dumps(run_smart_garbage_collector(), indent=2, ensure_ascii=False))
