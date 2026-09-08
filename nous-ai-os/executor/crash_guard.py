from executor.rollback import rollback
from executor.versions import last_version

def recover(file):
    v = last_version(file)
    if not v:
        return False
    rollback(v["content"], file)
    return True
