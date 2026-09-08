from executor.memory import set_mem, get_mem, all_mem

class Orchestrator:

    def register_goal(self, goal):
        set_mem("goal", goal)
        return {"goal_set": goal}

    def remember(self, k, v):
        return set_mem(k, v)

    def recall(self, k):
        return get_mem(k)

    def full_memory(self):
        return all_mem()
