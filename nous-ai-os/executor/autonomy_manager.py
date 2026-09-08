from executor.autonomy import start
from executor.autonomy import stop
from executor.autonomy import status

def execute(action):

    if action=="start":
        return start()

    if action=="stop":
        return stop()

    return status()
