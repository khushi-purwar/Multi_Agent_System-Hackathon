from agents.base_agent import BaseAgent
import pandas as pd

class InsightAgent(BaseAgent):
    def __init__(self, name, llm):
        super().__init__(name)
        self.llm = llm

    def analyze_health(self, df: pd.DataFrame):
        prompt = f"""
        Analyze this elderly health dataset and highlight any concerning trends or issues.

        Dataset sample:
        {df.head(10).to_markdown()}
        """
        response = self.llm.query(prompt)
        print("\n[LLM Health Insights]\n", response)

    def process(self, row):
        pass  # Placeholder if needed later
