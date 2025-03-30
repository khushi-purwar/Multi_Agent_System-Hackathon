import sqlite3
from datetime import datetime
from .base_agent import BaseAgent

class HealthAgent(BaseAgent):
    def process(self, records: list):
        alert_count = 0
        MAX_LLM_ALERTS = 10

        for row in records:
            user_id = row[0]
            timestamp = row[1]
            heart_rate = row[2]
            heart_rate_threshold = row[3]
            bp = row[4]
            bp_threshold = row[5]
            glucose = row[6]
            glucose_threshold = row[7]
            spo2 = row[8]
            oxygen_threshold = row[9]
            alert_flag = row[10]

            # Process only records with an abnormal alert (alert_flag == "Yes")
            if alert_flag.strip().lower() == "yes" and alert_count < MAX_LLM_ALERTS:
                detailed_prompt = (
                    f"User has the following readings:\n"
                    f"- Heart Rate = {heart_rate} bpm and " +
                    ("which is normal" if heart_rate_threshold.strip().lower() == "no" else "which is not normal") + ".\n"
                    f"- Blood Pressure = {bp} and " + 
                    ("which is normal" if bp_threshold.strip().lower() == "no" else "which is not normal") + ".\n"
                    f"- Glucose Level = {glucose} and " + 
                    ("which is normal" if glucose_threshold.strip().lower() == "no" else "which is not normal") + ".\n"
                    f"- Oxygen Saturation = {spo2}. and " +
                    ("which is normal" if oxygen_threshold.strip().lower() == "no" else "which is not normal") + ".\n"
                    "Please provide the appropriate action in 1 or 2 lines"
                )
                self.log_to_llm(detailed_prompt, user_id)
                alert_count += 1
