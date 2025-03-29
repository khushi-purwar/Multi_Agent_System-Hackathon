from agents.base_agent import BaseAgent
import sqlite3

class ReminderAgent(BaseAgent):
    def process(self, row):
        reminder_text = f"Reminder for {row['Device-ID/User-ID']}: {row['Reminder Type']} at {row['Scheduled Time']}."
        speak(reminder_text) 

        conn = sqlite3.connect("elderly_care.db")
        conn.execute("INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?)", (
            row['Device-ID/User-ID'], row['Timestamp'], row['Reminder Type'],
            row['Scheduled Time'], row['Reminder Sent (Yes/No)'],
            row['Acknowledged (Yes/No)']
        ))
        conn.commit()
        conn.close()
