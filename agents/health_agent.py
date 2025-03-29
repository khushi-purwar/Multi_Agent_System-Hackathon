from agents.base_agent import BaseAgent
import sqlite3

class HealthAgent(BaseAgent):
    def process(self, row):
        alert = "No"
        if row['Heart Rate Below/Above Threshold (Yes/No)'] == 'Yes':
            alert = "Yes"
        elif row['Blood Pressure Below/Above Threshold (Yes/No)'] == 'Yes':
            alert = "Yes"
        elif row['Glucose Levels Below/Above Threshold (Yes/No)'] == 'Yes':
            alert = "Yes"

        conn = sqlite3.connect("elderly_care.db")
        conn.execute("INSERT INTO health VALUES (?, ?, ?, ?, ?, ?, ?)", (
            row['Device-ID/User-ID'], row['Timestamp'], row['Heart Rate'],
            row['Blood Pressure'], row['Glucose Levels'],
            row['Oxygen Saturation (SpO₂%)'], alert
        ))
        conn.commit()
        conn.close()
