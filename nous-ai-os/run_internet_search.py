import sys, json
from executor.internet_search_engine import answer_from_web
print(json.dumps(answer_from_web(" ".join(sys.argv[1:])), indent=2, ensure_ascii=False))
