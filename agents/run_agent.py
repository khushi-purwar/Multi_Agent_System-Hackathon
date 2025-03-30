import os
import pandas as pd
from agents.health_agent import HealthAgent
from agents.reminder_agent import ReminderAgent
from agents.safety_agent import SafetyAgent
from db import fetch_records

class RunAgent:
    def run_agents(self):
        health_df = fetch_records("health")
        health_agent = HealthAgent("HealthAgent")

        reminder_df = fetch_records("reminders")
        reminder_agent = ReminderAgent("ReminderAgent")

        safety_df = fetch_records("safety")
        safety_agent = SafetyAgent("SafetyAgent")

        if health_df:
            health_agent.process(health_df)
        if reminder_df:
            reminder_agent.process(reminder_df)
        if safety_df:
            safety_agent.process(safety_df)

        health_agent.shutdown()
        reminder_agent.shutdown()
        safety_agent.shutdown()

        # If using a background worker, wait for the queue to finish processing:
        from llm_queue_worker import llm_prompt_queue
        print("Waiting for LLM queue to finish...")
        llm_prompt_queue.join()
