import sys, json
from executor.deep_research_engine import deep_research

q = " ".join(sys.argv[1:])
print(json.dumps(deep_research(q), indent=2, ensure_ascii=False))
