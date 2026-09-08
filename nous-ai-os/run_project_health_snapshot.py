from executor.project_health_snapshot import run_project_health_snapshot
import json
print(json.dumps(run_project_health_snapshot(), indent=2, ensure_ascii=False))
