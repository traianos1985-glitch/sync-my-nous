from executor.patch_pipeline_manager import run_patch_pipeline_manager
import json

print(json.dumps(run_patch_pipeline_manager(), indent=2, ensure_ascii=False))
