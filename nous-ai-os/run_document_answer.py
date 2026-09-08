import sys
import json
from executor.document_answer_engine import answer_question, document_answer_status

if len(sys.argv) == 1:
    print(json.dumps(document_answer_status(), indent=2, ensure_ascii=False))
else:
    print(json.dumps(answer_question(" ".join(sys.argv[1:])), indent=2, ensure_ascii=False))
