import pandas as pd
import sqlite3
import os
import pyttsx3
from datetime import datetime
from typing import Dict, Any
from llm_coordinator import LLMCoordinator
from rich.console import Console
from rich.table import Table

# === Global Data Directory ===
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# === SQLite Initialization ===
def init_db():
    conn = sqlite3.connect("elderly_care.db")
    cursor = conn.cursor()

    # Health table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health (
            user_id TEXT, timestamp TEXT, heart_rate INT,
            bp TEXT, glucose INT, spo2 INT, alert TEXT
        )
    ''')

    # Safety table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS safety (
            user_id TEXT, timestamp TEXT, activity TEXT,
            fall_detected TEXT, location TEXT, alert TEXT
        )
    ''')

    # Reminder table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            user_id TEXT, timestamp TEXT, reminder_type TEXT,
            scheduled_time TEXT, sent TEXT, acknowledged TEXT
        )
    ''')

    # Agent communication log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_communications (
            sender TEXT, message TEXT, response TEXT, timestamp TEXT
        )
    ''')

    conn.commit()
    conn.close()

# === Agent Base Class ===
class BaseAgent:
    def __init__(self, name: str, coordinator=None):
        self.name = name
        self.coordinator = coordinator

    def process(self, data: Dict[str, Any]):
        raise NotImplementedError

# === Health Agent ===
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

        if alert == "Yes" and self.coordinator:
            message = f"User {row['Device-ID/User-ID']} has abnormal health readings (HR/BP/Glucose) at {row['Timestamp']}. Should we alert caregiver or check reminders?"
            response = self.coordinator.ask(self.name, message)
            conn.execute("INSERT INTO agent_communications VALUES (?, ?, ?, ?)", (
                self.name, message, response, datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

# === Safety Agent ===
class SafetyAgent(BaseAgent):
    def process(self, row):
        alert = row['Alert Triggered (Yes/No)']
        conn = sqlite3.connect("elderly_care.db")
        conn.execute("INSERT INTO safety VALUES (?, ?, ?, ?, ?, ?)", (
            row['Device-ID/User-ID'], row['Timestamp'],
            row['Movement Activity'], row['Fall Detected (Yes/No)'],
            row['Location'], alert
        ))

        if alert == "Yes" and self.coordinator:
            message = f"User {row['Device-ID/User-ID']} triggered a fall or abnormal activity alert at {row['Timestamp']} in {row['Location']}. Should family be informed or a check scheduled?"
            response = self.coordinator.ask(self.name, message)
            conn.execute("INSERT INTO agent_communications VALUES (?, ?, ?, ?)", (
                self.name, message, response, datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

# === Reminder Agent ===
class ReminderAgent(BaseAgent):
    def process(self, row):
        conn = sqlite3.connect("elderly_care.db")
        conn.execute("INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?)", (
            row['Device-ID/User-ID'], row['Timestamp'], row['Reminder Type'],
            row['Scheduled Time'], row['Reminder Sent (Yes/No)'],
            row['Acknowledged (Yes/No)']
        ))
        conn.commit()
        conn.close()

# === Coordinator ===
def run_agents():
    def read_csv_safe(filename):
        full_path = os.path.join(DATA_DIR, filename)
        if os.path.exists(full_path):
            return pd.read_csv(full_path, encoding='utf-8')
        else:
            print(f"[WARNING] File not found: {full_path}")
            return pd.DataFrame()

    health_df = read_csv_safe("health_monitoring.csv")
    safety_df = read_csv_safe("safety_monitoring.csv")
    reminder_df = read_csv_safe("daily_reminder.csv")

    llm_coordinator = LLMCoordinator()

    health_agent = HealthAgent("HealthAgent", llm_coordinator)
    safety_agent = SafetyAgent("SafetyAgent", llm_coordinator)
    reminder_agent = ReminderAgent("ReminderAgent")

    for _, row in health_df.iterrows():
        health_agent.process(row)

    for _, row in safety_df.iterrows():
        safety_agent.process(row)

    for _, row in reminder_df.iterrows():
        reminder_agent.process(row)

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()

if __name__ == "__main__":
    init_db()
    run_agents()

    # Show LLM Communication Logs
    console = Console()

    conn = sqlite3.connect("elderly_care.db")
    cursor = conn.cursor()
    cursor.execute("SELECT sender, message, response, timestamp FROM agent_communications")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        table = Table(title="🧠 LLM Agent Communications", show_lines=True)
        table.add_column("Sender", style="cyan", no_wrap=True)
        table.add_column("Message", style="yellow")
        table.add_column("LLM Response", style="green")
        table.add_column("Timestamp", style="magenta")

        for sender, message, response, timestamp in rows:
            table.add_row(sender, message, response, timestamp)

        console.print(table)
    else:
        console.print("[bold green]✅ All agents processed data. No alerts triggered communication.[/bold green]")

