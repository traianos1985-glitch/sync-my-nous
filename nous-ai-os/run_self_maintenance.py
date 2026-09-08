from executor.self_maintenance_engine import run_self_maintenance
import json

print(json.dumps(run_self_maintenance(), indent=2, ensure_ascii=False))
