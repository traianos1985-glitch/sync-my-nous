import sys, json
from executor.url_reader_engine import summarize_url

url = " ".join(sys.argv[1:])
print(json.dumps(summarize_url(url), indent=2, ensure_ascii=False))
