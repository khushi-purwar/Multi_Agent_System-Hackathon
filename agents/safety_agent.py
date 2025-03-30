import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from llm_queue_worker import llm_prompt_queue

class SafetyAgent(BaseAgent):
    def __init__(self, name="SafetyAgent", enable_llm=True):
        super().__init__(name, enable_llm)
        self.alert_count = 0
        self.MAX_ALERTS = 10

    def process(self, records: list):
        now = datetime.now()

        for row in records:
            user_id, timestamp, activity, fall_detected, impact_force_level, post_fall_inactivity_duration, location, alert_triggered, caregiver_notified = row

            try:
                fall = fall_detected.strip().lower()
                impact = impact_force_level.strip().lower()
                alert_triggered = alert_triggered.strip().lower()
                movement = activity.strip().lower()
                location = location.strip().lower()
                caregiver_notified = caregiver_notified.strip().lower()

                inactivity_seconds = int(post_fall_inactivity_duration)
                message = None

                # === CASE 1: Fall with impact and inactivity ===
                if (
                    fall == "yes"
                    and impact in ("medium", "high")
                    and inactivity_seconds > 30
                    and alert_triggered == "no"
                    and self.alert_count < self.MAX_ALERTS
                ):
                    message = (
                        f"Fall detected for user {user_id} at {location}. Impact level: {impact}. "
                        f"Inactivity duration: {inactivity_seconds} seconds. Immediate check required."
                    )

                # === CASE 2: Lying in bathroom or kitchen ===
                elif (
                    movement == "lying"
                    and location in ("bathroom", "kitchen")
                    and alert_triggered == "no"
                    and self.alert_count < self.MAX_ALERTS
                ):
                    message = (
                        f"User {user_id} is lying in the {location}. Check if the user needs assistance."
                    )

                # === CASE 3: No movement detected at all for extended time ===
                elif (
                    movement == "none"
                    and inactivity_seconds > 1800  # 30 minutes
                    and alert_triggered == "no"
                    and self.alert_count < self.MAX_ALERTS
                ):
                    message = (
                        f"No movement detected for user {user_id} for the last {inactivity_seconds//60} minutes. "
                        f"Location: {location}. Consider checking in."
                    )

                # === CASE 4: Fall detected but no movement at all ===
                elif (
                    fall == "yes"
                    and movement == "none"
                    and alert_triggered == "no"
                    and self.alert_count < self.MAX_ALERTS
                ):
                    message = (
                        f"Fall detected for user {user_id} with no subsequent movement. Immediate attention required at {location}."
                    )

                if message:
                    self.log_to_llm(message, user_id)
                    if fall == "yes": 
                        self._trigger_voice_alert(message)
                    self.alert_count += 1

            except Exception as e:
                print(f"[SafetyAgent] Error processing safety row: {e}")

    def _trigger_voice_alert(self, message):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(message)
            engine.runAndWait()
            print("[SafetyAgent] 🔊 Voice alert triggered.")
        except Exception as e:
            pass  # Silently ignore voice failures
