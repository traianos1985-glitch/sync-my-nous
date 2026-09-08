import time

from executor.battery_guard import battery_guard
from executor.daily_brief import daily_brief
from executor.scheduler_agent import list_schedules, run_due_schedules
from executor.agent_review import review_last

def autonomy_cycle():
    result = {
        "time": time.time(),
        "battery": battery_guard(),
        "daily_brief": daily_brief(),
        "scheduled": list_schedules(),
        "scheduled_executed": run_due_schedules(),
        "review": review_last()
    }

    return result
