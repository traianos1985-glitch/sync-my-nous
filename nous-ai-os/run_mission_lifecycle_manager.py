from executor.mission_lifecycle_manager import run_mission_lifecycle_manager
import json
print(json.dumps(run_mission_lifecycle_manager(), indent=2, ensure_ascii=False))
