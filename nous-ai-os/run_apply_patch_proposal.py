import sys
import json
from executor.patch_apply_engine import apply_patch_proposal

if len(sys.argv) < 2:
    print(json.dumps({
        "ok": False,
        "error": "missing_proposal_id",
        "usage": "python run_apply_patch_proposal.py <proposal_id>"
    }, indent=2, ensure_ascii=False))
    raise SystemExit(1)

proposal_id = sys.argv[1]
print(json.dumps(apply_patch_proposal(proposal_id), indent=2, ensure_ascii=False))
