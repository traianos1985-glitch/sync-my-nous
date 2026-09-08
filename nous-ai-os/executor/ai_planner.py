from executor.memory import load_memory

class AIPlanner:

    def __init__(self):

        self.memory = load_memory()

    def analyze_goals(self):

        goals = self.memory.get("goals", [])

        plans = []

        for item in goals:

            goal = item.get("goal", "")

            if "autonomous" in goal.lower():

                plans.append({
                    "goal": goal,
                    "priority": "HIGH",
                    "actions": [
                        "build evolution engine",
                        "enable self-improvement",
                        "create plugin system",
                        "integrate local llm"
                    ]
                })

            else:

                plans.append({
                    "goal": goal,
                    "priority": "NORMAL",
                    "actions": [
                        "analyze goal",
                        "create execution plan"
                    ]
                })

        return plans
