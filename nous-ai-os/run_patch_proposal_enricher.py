from executor.patch_proposal_enricher import run_patch_proposal_enricher
import json

print(json.dumps(run_patch_proposal_enricher(), indent=2, ensure_ascii=False))
