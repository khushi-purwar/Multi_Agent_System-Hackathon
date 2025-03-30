import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
from datetime import datetime

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

@st.cache_data
def get_llm_logs():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM agent_communications ORDER BY timestamp DESC", conn)
    conn.close()
    return df

# === UI Layout ===
st.set_page_config(page_title="Elderly Care AI Dashboard", layout="wide")
st.title("👵 Elderly Care Multi-Agent Dashboard")

# === Sidebar ===
st.sidebar.header("📂 View Tables")
table_choice = st.sidebar.selectbox("Select a table", ["Health", "Safety", "Reminders"])

# === Main Tabs ===
tabs = st.tabs(["📊 Data Viewer", "🧠 Agent Activity"])

# === Tab 1: Data Viewer ===
with tabs[0]:
    st.subheader(f"📋 {table_choice.capitalize()} Table")
    df = load_table(table_choice)
    if not df.empty:
        page_size = 20  # rows per page
        total_pages = (len(df) - 1) // page_size + 1

        page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size

        st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)
        st.caption(f"Showing {start_idx + 1} to {min(end_idx, len(df))} of {len(df)} rows")
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
                SELECT user_id, message, response, timestamp, sender
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
    st.caption(f"Showing logs for: **{table_choice.capitalize()} Agent**")

    # Filters
    user_filter = st.text_input("🔍 Filter by User ID:")

    if not logs_df.empty:
        if user_filter:
            filtered_df = logs_df[logs_df['user_id'].astype(str).str.contains(user_filter, case=False, na=False)]
        else:
            filtered_df = logs_df

        # Table    
        st.dataframe(filtered_df, use_container_width=True)

        st.markdown("<h2 style='font-size:16px;'>🚨 Alerts by Severity (from LLM)</h2>", unsafe_allow_html=True)
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

        st.dataframe(df[[ 'user_id', 'message', 'Severity']])

    else:
        st.info("No agent communications yet for this category.")
        
