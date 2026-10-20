class StudyPlanner:
    def __init__(self, learner: str):
        self.learner = learner

def plan(self, topic: str) -> str:
    topic = topic.strip()
    if not topic:
        raise ValueError("topic must not be empty")
    return f"{self.learner}: {topic}"

if __name__ == "__main__":
    planner = StudyPlanner("student")
    print(planner.plan("Python basics"))