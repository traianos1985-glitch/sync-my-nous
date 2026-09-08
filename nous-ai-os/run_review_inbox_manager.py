from executor.review_inbox_manager import run_review_inbox_manager
import json
print(json.dumps(run_review_inbox_manager(), indent=2, ensure_ascii=False))
