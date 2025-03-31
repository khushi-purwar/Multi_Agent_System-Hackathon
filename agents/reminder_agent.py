import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from llm_queue_worker import llm_prompt_queue

class ReminderAgent(BaseAgent):
    def __init__(self, name="ReminderAgent", enable_llm=True):
        super().__init__(name, enable_llm)

    def _send_voice_reminder(self, message):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(message)
            engine.runAndWait()
            print(f"[ReminderAgent] ✅ Voice reminder sent.")
        except Exception as e:
            pass
    
    def _format_time(self, time_str):
        try:
            t = datetime.strptime(time_str, "%H:%M:%S")
            return t.strftime("%I:%M %p").lstrip("0").replace(":00", "")
        except Exception:
            return time_str 

    def process(self, records: list):
        grace_period = timedelta(minutes=5)
        alert_count = 0
        MAX_LLM_ALERTS = 30

        for row in records:
            user_id, timestamp, reminder_type, scheduled_time, reminder_sent, acknowledged = row

            try:
                now_dt = datetime.now()
                today = now_dt.date()

                # Parse the scheduled_time as a time, then combine with today's date
                scheduled_time_dt = datetime.combine(today, datetime.strptime(scheduled_time, "%H:%M:%S").time())

                scheduled_time_obj = datetime.strptime(scheduled_time, "%H:%M:%S").time()
                spoken_time = scheduled_time_obj.strftime("%I").lstrip("0") + " o'clock"

                reminder_sent = reminder_sent.strip().lower()
                acknowledged = acknowledged.strip().lower()

                # === CASE 1: Scheduled Reminder (due now)
                if reminder_sent == "no" and scheduled_time_dt <= now_dt and alert_count < MAX_LLM_ALERTS:
                    prompt = f"Generate a short and friendly reminder for an elderly person: {reminder_type} is scheduled now."
                    llm_prompt_queue.put((self.name, prompt, user_id))
                    
                    spoken_message = f"Reminder: {reminder_type} is scheduled now for {self._format_time(scheduled_time)}."
                    self._send_voice_reminder(spoken_message)
                    alert_count += 1

                # === CASE 2: Not Acknowledged (past grace period)
                elif reminder_sent == "yes" and acknowledged == "no" and now_dt > (scheduled_time_dt + grace_period) and alert_count < MAX_LLM_ALERTS:
                    escalation_prompt = f"Reminder for '{reminder_type}' was sent to user {user_id} but not acknowledged. Escalate gently."
                    llm_prompt_queue.put((self.name, prompt, user_id))
                    
                    escalation_message = f"You still need to acknowledge your {reminder_type} reminder from {self._format_time(scheduled_time)}."
                    self._send_voice_reminder(escalation_message)
                    alert_count += 1

            except Exception as e:
                print(f"[ReminderAgent] Error processing reminder: {e}")
