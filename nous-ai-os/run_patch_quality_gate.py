import sys, json
from executor.patch_quality_gate import quality_gate

print(json.dumps(quality_gate(sys.argv[1:] or None, label="manual_cli"), indent=2, ensure_ascii=False))
