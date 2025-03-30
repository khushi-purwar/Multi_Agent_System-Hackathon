import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "elderly_care.db")
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATA_DIR = os.path.abspath(DATA_DIR)
print(f"DATA_DIR: {DATA_DIR}")

## read daat from csv file and insert the data into database
def read_csv_and_insert(filename, table_name):
    full_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(full_path):
        try:
            df = pd.read_csv(full_path, encoding='utf-8')

            # handle extra columns
            if (table_name == "reminders" or  table_name == "safety" or table_name == "health") and df.shape[1] > 6:
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            records = [tuple(row) for row in df.itertuples(index=False, name=None)]
                
            # Insert the records into the specified table
            insert_data(table_name, records)
            print(f"[INFO] Inserted data into table '{table_name}'.")
        except Exception as e:
            print(f"[ERROR] Could not read {filename}: {e}")
    else:
        print(f"[WARNING] File not found: {full_path}")

#  intialize the database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS health (
                        user_id TEXT, 
                        timestamp TEXT, 
                        heart_rate INT, 
                        hear_rate_threshold_flag TEXT,
                        bp TEXT, 
                        bp_threshold_flag TEXT,
                        glucose INT,
                        glucose_Threshold_flag TEXT, 
                        oxygen INT, 
                        oxygen_threshold_flag TEXT,
                        alert_triggered TEXT,
                        caregiver_notified TEXT
                        )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS safety (
                        user_id TEXT, 
                        timestamp TEXT, 
                        activity TEXT, 
                        fall_detected TEXT, 
                        impact_force_level TEXT,
                        post_fall_inactivity_duration INT,
                        location TEXT, 
                        alert_triggered TEXT,
                        caregiver_notified TEXT
                        )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (
                        user_id TEXT, 
                        timestamp TEXT, 
                        reminder_type TEXT, 
                        scheduled_time TEXT, 
                        sent TEXT, 
                        acknowledged TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS agent_communications (
                        sender TEXT, 
                        user_id TEXT,  
                        message TEXT, 
                        response TEXT, 
                        timestamp TEXT)''')
                        
    read_csv_and_insert("health_monitoring.csv", "health")
    read_csv_and_insert("safety_monitoring.csv", "safety")
    read_csv_and_insert("daily_reminder.csv", "reminders")

    conn.commit()
    conn.close()

def insert_data(table_name, records):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if table_name == "health":
        cursor.executemany("INSERT INTO health VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", records)
    elif table_name == "safety":
        cursor.executemany("INSERT INTO safety VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", records)
    elif table_name == "reminders":
        cursor.executemany("INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?)", records)
    else:
        print(f"Unknown table: {table_name}")
        conn.close()
        return
    
    conn.commit()
    conn.close()


def fetch_records(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    records = cursor.fetchall()
    conn.close()
    return records


