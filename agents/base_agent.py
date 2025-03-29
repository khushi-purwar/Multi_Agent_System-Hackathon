class BaseAgent:
    def __init__(self, name):
        self.name = name

    def process(self, row):
        raise NotImplementedError("Each agent must implement the process method.")