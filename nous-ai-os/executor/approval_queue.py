APPROVAL_QUEUE = {}

def create_request(action, data):

    req_id = str(len(APPROVAL_QUEUE) + 1)

    APPROVAL_QUEUE[req_id] = {
        "action": action,
        "data": data,
        "status": "pending"
    }

    return req_id


def approve(req_id):

    if req_id in APPROVAL_QUEUE:

        APPROVAL_QUEUE[req_id]["status"] = "approved"

        return True

    return False


def reject(req_id):

    if req_id in APPROVAL_QUEUE:

        APPROVAL_QUEUE[req_id]["status"] = "rejected"

        return True

    return False


def get_pending():

    return {
        k: v for k, v in APPROVAL_QUEUE.items()
        if v["status"] == "pending"
    }
