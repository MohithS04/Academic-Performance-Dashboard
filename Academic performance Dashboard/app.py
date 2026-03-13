import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Academic Performance Dashboard", layout="wide", page_icon="🎓")

DB_FILE = 'academic_data.db'

# Use st.cache_resource for the database connection so we don't reconnect constantly
@st.cache_resource
def get_db_connection():
    # check_same_thread=False is needed for Streamlit caching with sqlite
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def load_data():
    conn = get_db_connection()
    try:
        df_students = pd.read_sql_query("SELECT * FROM students", conn)
        df_attendance = pd.read_sql_query("SELECT * FROM attendance", conn)
        df_performance = pd.read_sql_query("SELECT * FROM performance", conn)
        return df_students, df_attendance, df_performance
    except pd.errors.DatabaseError:
        # DB might not exist yet or tables missing
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# Set up auto-refresh
refresh_rate = st.sidebar.slider("Data Refresh Rate (seconds)", 1, 60, 5)

st.title("🎓 Academic Performance Dashboard")
st.markdown("Real-time monitoring of student metrics, attendance, and data integrity.")

df_students, df_attendance, df_performance = load_data()

if df_students.empty:
    st.warning("No data found. Please ensure `data_simulator.py` is running to generate real-time data.")
    st.stop()

# --- KPIs ---
st.header("Executive Overview")
col1, col2, col3, col4 = st.columns(4)

total_students = len(df_students)
avg_score = df_performance['score'].mean() if not df_performance.empty else 0
total_attendance_records = len(df_attendance)

# Calculate attendance rate
if not df_attendance.empty:
    present_count = len(df_attendance[df_attendance['status'] == 'Present'])
    attendance_rate = (present_count / total_attendance_records) * 100
else:
    attendance_rate = 0

col1.metric("Total Enrolled Students", f"{total_students:,}")
col2.metric("Average GPA (Score %)", f"{avg_score:.2f}%")
col3.metric("Overall Attendance Rate", f"{attendance_rate:.1f}%")
col4.metric("Total Events Logged", f"{(total_attendance_records + len(df_performance)):,}")


st.markdown("---")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Enrollment & Attendance", "📈 Student Performance", "🛠️ Data Validation & Integrity"])

# Tab 1: Enrollment & Attendance
with tab1:
    st.subheader("Enrollment Trends")
    if not df_students.empty and 'enrollment_date' in df_students.columns:
        df_students['enrollment_date'] = pd.to_datetime(df_students['enrollment_date'], format='mixed')
        # Sort values and set index
        enrollment_trend = df_students.sort_values('enrollment_date').set_index('enrollment_date')
        
        # We need a simple count over time for a line chart
        enrollment_trend['count'] = 1
        # cumulative sum over time
        enrollment_trend['Cumulative Enrollment'] = enrollment_trend['count'].cumsum()
        
        fig_enroll = px.line(enrollment_trend.reset_index(), x='enrollment_date', y='Cumulative Enrollment', 
                             title="Cumulative Student Enrollment Over Time")
        st.plotly_chart(fig_enroll, use_container_width=True)
        
    st.subheader("Recent Attendance Distribution")
    if not df_attendance.empty:
        att_counts = df_attendance['status'].value_counts().reset_index()
        att_counts.columns = ['Status', 'Count']
        fig_att = px.pie(att_counts, names='Status', values='Count', title="Attendance Status Breakdown", hole=0.3)
        st.plotly_chart(fig_att, use_container_width=True)

# Tab 2: Student Performance
with tab2:
    st.subheader("Performance by Subject")
    if not df_performance.empty:
        # Filter out extreme anomalies just for the 'clean' chart, or show them to be transparent
        # I will show them for transparency, but limit view realistically
        fig_perf = px.box(df_performance, x="subject", y="score", color="subject", 
                          title="Grade Distribution By Subject", points="all")
        st.plotly_chart(fig_perf, use_container_width=True)
        
        st.subheader("Latest Top Performers")
        # Join performance with students
        merged_perf = df_performance.merge(df_students, on='student_id', how='left')
        latest_perf = merged_perf.sort_values('exam_date', ascending=False).head(10)
        st.dataframe(latest_perf[['first_name', 'last_name', 'subject', 'score', 'exam_date', 'grade_level']])
        
# Tab 3: Data Validation & Integrity
with tab3:
    st.subheader("Automated Data Validation Workflows")
    st.markdown("The system automatically scans for anomalies and highlights data integrity issues.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("#### Performance Anomalies")
        st.markdown("**Rule 1:** Scores must be between 0 and 100.")
        if not df_performance.empty:
            anomalies_perf = df_performance[(df_performance['score'] < 0) | (df_performance['score'] > 100)]
            st.metric("Detected Grade Anomalies", len(anomalies_perf))
            if not anomalies_perf.empty:
                st.dataframe(anomalies_perf)
            else:
                st.success("No grade anomalies detected!")
                
    with col_b:
        st.markdown("#### Attendance Orphans")
        st.markdown("**Rule 2:** Attendance records must link to a valid student ID.")
        if not df_attendance.empty and not df_students.empty:
            valid_ids = df_students['student_id'].unique()
            anomalies_att = df_attendance[~df_attendance['student_id'].isin(valid_ids)]
            st.metric("Detected Orphan Attendance Logs", len(anomalies_att))
            if not anomalies_att.empty:
                st.dataframe(anomalies_att)
            else:
                st.success("No orphaned attendance records!")


# To achieve real-time refresh, we rerun the Streamlit script automatically
time.sleep(refresh_rate)
st.rerun()
