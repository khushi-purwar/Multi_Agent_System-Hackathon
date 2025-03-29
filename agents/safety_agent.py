from agents.base_agent import BaseAgent
import sqlite3

class SafetyAgent(BaseAgent):
    def process(self, row):
        alert = row['Alert Triggered (Yes/No)']
        conn = sqlite3.connect("elderly_care.db")
        conn.execute("INSERT INTO safety VALUES (?, ?, ?, ?, ?, ?)", (
            row['Device-ID/User-ID'], row['Timestamp'],
            row['Movement Activity'], row['Fall Detected (Yes/No)'],
            row['Location'], alert
        ))
        conn.commit()
        conn.close()
