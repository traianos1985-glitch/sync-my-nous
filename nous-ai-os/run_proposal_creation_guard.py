from executor.proposal_creation_guard import run_proposal_creation_guard
import json
print(json.dumps(run_proposal_creation_guard(), indent=2, ensure_ascii=False))
