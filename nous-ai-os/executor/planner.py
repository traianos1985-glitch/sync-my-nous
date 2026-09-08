def make_plan(goal):
    goal = str(goal)
    return {
        "goal": goal,
        "steps": [
            "analyze_request",
            "choose_tool_or_reasoning",
            "execute_safely",
            "store_result",
            "report_to_user"
        ],
        "status": "planned"
    }
