import streamlit as st
import pandas as pd
import sqlite3
import os

# === SQLite Setup ===
DB_PATH = "elderly_care.db"

@st.cache_data
def load_table(table_name):
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading {table_name}: {e}")
        return pd.DataFrame()

# === UI Layout ===
st.set_page_config(page_title="Elderly Care AI Dashboard", layout="wide")
st.title("👵 Elderly Care Multi-Agent Dashboard")

# === Sidebar ===
st.sidebar.header("📂 View Tables")
table_choice = st.sidebar.selectbox("Select a table", ["health", "safety", "reminders"])

# === Main Tabs ===
tabs = st.tabs(["📊 Data Viewer", "🧠 Agent Activity", "🔊 Voice Alerts", "📞 Family Alerts"])

# === Tab 1: Data Viewer ===
with tabs[0]:
    st.subheader(f"📋 {table_choice.capitalize()} Table")
    df = load_table(table_choice)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No data found.")

# === Tab 2: Agent Activity (Placeholder for logs) ===
with tabs[1]:
    st.subheader("🧠 Agent Communication Logs")

    @st.cache_data
    def load_logs_by_agent(agent_type):
        agent_map = {
            "health": "HealthAgent",
            "safety": "SafetyAgent",
            "reminders": "ReminderAgent"
        }
        agent_name = agent_map.get(agent_type.lower(), "")
        if not os.path.exists(DB_PATH):
            return pd.DataFrame()
        try:
            conn = sqlite3.connect(DB_PATH)
            query = f"""
                SELECT sender, message, response, timestamp 
                FROM agent_communications 
                WHERE sender = '{agent_name}'
                ORDER BY timestamp DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error loading logs: {e}")
            return pd.DataFrame()

    logs_df = load_logs_by_agent(table_choice)
    st.caption(f"Showing logs for: **{table_choice.capitalize()}Agent**")

    if not logs_df.empty:
        st.dataframe(logs_df, use_container_width=True)
    else:
        st.info("No agent communications yet for this category.")


# === Tab 3: Voice Alerts (Text to Speech) ===
with tabs[2]:
    st.subheader("🔊 Send Voice Reminder")
    message = st.text_input("Enter reminder message")
    if st.button("Send Voice Message"):
        os.system(f"say {message}")  # For macOS; for Windows, integrate pyttsx3
        st.success("Voice reminder triggered")

# === Tab 4: Family Alerts (Twilio Placeholder) ===
with tabs[3]:
    st.subheader("📞 Notify Family")
    test_message = st.text_input("Enter emergency alert")
    if st.button("Send SMS (Test)"):
        st.info("This would trigger Twilio SMS (to be integrated)")
