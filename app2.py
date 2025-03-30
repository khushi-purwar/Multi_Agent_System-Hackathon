import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

DB_PATH = "elderly_care.db"

@st.cache_data
def load_table(table):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

@st.cache_data
def get_llm_logs():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM agent_communications ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def agent_summary():
    health = load_table("health")
    safety = load_table("safety")
    reminders = load_table("reminders")
    comms = get_llm_logs()

    st.subheader("📊 Agent Processing Summary")
    summary = pd.DataFrame({
        "Agent": ["HealthAgent", "SafetyAgent", "ReminderAgent"],
        "Total Records": [len(health), len(safety), len(reminders)],
        "LLM Alerts": [
            comms[comms.sender == "HealthAgent"].shape[0],
            comms[comms.sender == "SafetyAgent"].shape[0],
            comms[comms.sender == "ReminderAgent"].shape[0],
        ]
    })
    st.dataframe(summary)

def llm_activity():
    st.subheader("🤖 LLM Recent Activity")
    df = get_llm_logs()

    # Filters
    user_filter = st.text_input("🔍 Filter by User ID (in message):")
    time_range = st.slider("⏱️ Select Time Range (minutes ago):", 0, 1440, 60)

    if user_filter:
        df = df[df.message.str.contains(user_filter, case=False)]

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    min_time = datetime.now() - pd.to_timedelta(time_range, unit='m')
    df = df[df.timestamp >= min_time]

    # Display table
    st.dataframe(df[['timestamp', 'sender', 'message', 'response']])

    # Graph
    fig = px.histogram(df, x="timestamp", color="sender", nbins=30, title="LLM Activity Over Time")
    st.plotly_chart(fig, use_container_width=True)

def alerts_dashboard():
    st.subheader("🚨 Alerts by Severity (from LLM)")
    df = get_llm_logs()

    # Simple severity tag based on response text (can be made more sophisticated)
    def severity_level(resp):
        if not resp: return "Unknown"
        resp_lower = resp.lower()
        if any(w in resp_lower for w in ["immediate", "emergency", "critical"]):
            return "High"
        elif any(w in resp_lower for w in ["should", "check", "notify"]):
            return "Medium"
        else:
            return "Low"

    df['Severity'] = df['response'].apply(severity_level)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    st.dataframe(df[['timestamp', 'sender', 'message', 'Severity']])

    fig = px.histogram(df, x="timestamp", color="Severity", title="Alerts by Severity Over Time")
    st.plotly_chart(fig, use_container_width=True)

st.set_page_config(layout="wide", page_title="Elderly Care Agent Dashboard")
st.title("🧓 Multi-Agent Elderly Care Dashboard")

agent_summary()
llm_activity()
alerts_dashboard()
