def repair_error(error):
    return {
        "status": "analyzed",
        "suggestion": "check syntax or imports",
        "error": str(error)
    }
