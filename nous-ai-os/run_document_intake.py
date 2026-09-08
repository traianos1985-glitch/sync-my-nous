import sys, json
from executor.document_intake_engine import ingest_file, search_documents, run_document_intake_status

if len(sys.argv) == 1:
    print(json.dumps(run_document_intake_status(), indent=2, ensure_ascii=False))
elif sys.argv[1] == "search":
    print(json.dumps(search_documents(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
else:
    print(json.dumps(ingest_file(sys.argv[1], note=" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
