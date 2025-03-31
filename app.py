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

# === Sidebar Navigation ===
st.sidebar.header("🔍 Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Data Viewer", "Agent Activity", "Visual Insights"])

# === Overview Page ===
if page == "Overview":
    st.subheader("📊 System Overview")

    st.markdown("""
    This Multi-Agentic AI System is designed to assist elderly individuals by providing real-time monitoring,
    reminders, and safety alerts. It promotes health management and social engagement through collaborative agent
    support. The system helps with:

    - 👨‍⚕️ **Health Monitoring:** Detects unusual behavior or health anomalies.
    - 🧠 **Reminder Management:** Provides reminders for medications, appointments, and daily routines.
    - 🚨 **Safety Alerts:** Triggers alerts during potential emergencies like falls or inactivity.
    - 🤝 **Collaboration:** Notifies caregivers, family, and healthcare providers in critical situations.
    - 💬 **LLM Assistance:** Agents use LLMs to generate contextual responses and assist in decision-making.
    """)

    logs = get_llm_logs()
    total_logs = len(logs)
    recent_logs = logs.head(5)

    st.metric("Total Agent Logs", total_logs)
    st.subheader("Recent 5 Agent Activities")
    st.dataframe(recent_logs, use_container_width=True)

    # Total entries by table
    table_stats = {}
    for table in ["Health", "Safety", "Reminders"]:
        df = load_table(table)
        table_stats[table] = len(df)

    st.subheader("📋 Data Records Summary")
    stats_df = pd.DataFrame.from_dict(table_stats, orient="index", columns=["Records"])
    st.bar_chart(stats_df)

# === Data Viewer Page ===
elif page == "Data Viewer":
    st.subheader("📋 View Table Data")
    table_choice = st.selectbox("*Select a table*", ["Health", "Safety", "Reminders"])
    df = load_table(table_choice)
    if not df.empty:
        st.markdown("*Select columns to display:*")
        selected_columns = st.multiselect("", options=df.columns.tolist())
        df = df[selected_columns] if selected_columns else df

        page_size = 20  # rows per page
        total_pages = (len(df) - 1) // page_size + 1
        page_num = st.number_input("*Page*", min_value=1, max_value=total_pages, value=1, step=1)
        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size
        st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)
        st.caption(f"Showing {start_idx + 1} to {min(end_idx, len(df))} of {len(df)} rows")
    else:
        st.warning("No data found.")

# === Agent Activity Logs ===
elif page == "Agent Activity":
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

    table_choice = st.selectbox("Select agent type", ["Health", "Safety", "Reminders"])
    logs_df = load_logs_by_agent(table_choice)
    st.caption(f"Showing logs for: **{table_choice.capitalize()} Agent**")

    user_filter = st.text_input("🔍 Filter by User ID:")

    if not logs_df.empty:
        if user_filter:
            filtered_df = logs_df[logs_df['user_id'].astype(str).str.contains(user_filter, case=False, na=False)]
        else:
            filtered_df = logs_df

        st.dataframe(filtered_df, use_container_width=True)

        st.markdown("<h2 style='font-size:16px;'>🚨 Alerts by Severity (from LLM)</h2>", unsafe_allow_html=True)
        df = get_llm_logs()

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

# === Visual Insights Page ===
elif page == "Visual Insights":
    st.subheader("📈 Visual Insights")

    llm_df = get_llm_logs()
    if not llm_df.empty:
        llm_df['timestamp'] = pd.to_datetime(llm_df['timestamp'])
        llm_df['hour'] = llm_df['timestamp'].dt.hour
        hourly_counts = llm_df.groupby('hour').size().reset_index(name='log_count')

        fig = px.line(hourly_counts, x='hour', y='log_count', title='LLM Agent Logs by Hour')
        st.plotly_chart(fig, use_container_width=True)

        agent_counts = llm_df['sender'].value_counts().reset_index()
        agent_counts.columns = ['Agent', 'Log Count']

        fig2 = px.pie(agent_counts, names='Agent', values='Log Count', title='Logs per Agent')
        st.plotly_chart(fig2, use_container_width=True)

        llm_df['msg_len'] = llm_df['message'].apply(lambda x: len(x.split()) if x else 0)
        fig3 = px.histogram(llm_df, x='msg_len', nbins=30, title='Distribution of Message Lengths')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No LLM logs found for visualizations.")