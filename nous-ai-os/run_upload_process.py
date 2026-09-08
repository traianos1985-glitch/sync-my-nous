import sys, json
from executor.upload_processing_engine import process_uploaded_file, upload_status

if len(sys.argv) < 2:
    print(json.dumps(upload_status(), indent=2, ensure_ascii=False))
else:
    print(json.dumps(process_uploaded_file(sys.argv[1], note=" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
