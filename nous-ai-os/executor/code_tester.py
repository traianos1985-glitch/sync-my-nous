import traceback

def test_plugin(code: str):

    try:
        local_env = {}

        exec(code, {}, local_env)

        if "run" not in local_env:
            return {
                "success": False,
                "error": "Missing run() function"
            }

        result = local_env["run"]()

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }
