import os
import pandas as pd
from agents.health_agent import HealthAgent
from db import fetch_records

class RunAgent:
    def run_agents(self):
        health_df = fetch_records("health")
        health_agent = HealthAgent("HealthAgent")

        if health_df:
            health_agent.process(health_df)

        health_agent.shutdown()

        # If using a background worker, wait for the queue to finish processing:
        from llm_queue_worker import llm_prompt_queue
        print("Waiting for LLM queue to finish...")
        llm_prompt_queue.join()
