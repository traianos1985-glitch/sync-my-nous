import sys, json
from executor.document_intelligence_engine import learn_file, answer_from_documents, status

if len(sys.argv) == 1:
    print(json.dumps(status(), indent=2, ensure_ascii=False))
elif sys.argv[1] == "ask":
    print(json.dumps(answer_from_documents(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
else:
    print(json.dumps(learn_file(sys.argv[1], note=" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
