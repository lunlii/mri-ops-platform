"""
Data Quality & Assumptions Page
"""

import duckdb
import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Data Quality & Assumptions", page_icon="✅", layout="wide")

DB_PATH = "data/mri_ops.duckdb"

@st.cache_data
def load_data():
    con = duckdb.connect(DB_PATH, read_only=True)
    appointments = con.execute("SELECT * FROM mart_ml_features").fetchdf()
    exam_logs    = con.execute("SELECT * FROM mart_ml_features").fetchdf()
    procedures   = con.execute("SELECT * FROM mart_procedure_variability").fetchdf()
    scanners     = con.execute("SELECT * FROM mart_daily_scanner_performance").fetchdf()
    con.close()
    return appointments, exam_logs, procedures, scanners

appointments, exam_logs, procedures, scanners = load_data()

st.title("✅ Data Quality & Assumptions")

# ── Dataset overview ──────────────────────────────────────────────────────────
st.subheader("Dataset Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Appointments",  f"{len(appointments):,}")
col2.metric("Exam Logs",     f"{len(exam_logs):,}")
col3.metric("Procedures",    f"{len(procedures):,}")
col4.metric("Scanners",      f"{len(scanners):,}")

# ── Null checks ───────────────────────────────────────────────────────────────
st.subheader("Null Value Checks")

def null_summary(df, name):
    nulls = df.isnull().sum()
    total = len(df)
    return pd.DataFrame({
        "Table": name,
        "Column": nulls.index,
        "Null Count": nulls.values,
        "Null %": (nulls.values / total * 100).round(2),
    })

null_df = pd.concat([
    null_summary(appointments, "stg_appointments"),
    null_summary(exam_logs,    "stg_exam_logs"),
]).query("`Null Count` > 0")

if len(null_df) == 0:
    st.success("✓ No null values found in any staging table.")
else:
    st.warning(f"{len(null_df)} columns with null values found.")
    st.dataframe(null_df, use_container_width=True, hide_index=True)

# ── Duration sanity checks ────────────────────────────────────────────────────
st.subheader("Duration Sanity Checks")

invalid_duration = exam_logs[exam_logs["actual_duration_min"] <= 0]
invalid_sequence = pd.DataFrame()

col1, col2 = st.columns(2)
col1.metric("Exams with duration ≤ 0", len(invalid_duration),
            delta="✓ None" if len(invalid_duration) == 0 else "⚠ Issues found")
col2.metric("Exams where end ≤ start", len(invalid_sequence),
            delta="✓ None" if len(invalid_sequence) == 0 else "⚠ Issues found")

# ── Distribution checks ────────────────────────────────────────────────────────
st.subheader("Actual Duration Distribution")

fig = px.histogram(
    exam_logs, x="actual_duration_min", nbins=60,
    title="Distribution of Actual Exam Durations",
    labels={"actual_duration_min": "Actual Duration (min)"},
    color_discrete_sequence=["#3498db"],
)
fig.update_layout(height=350)
st.plotly_chart(fig, use_container_width=True)

# ── Assumptions ───────────────────────────────────────────────────────────────
st.subheader("Key Assumptions & Design Decisions")

st.markdown("""
**Synthetic Data**
- All records are fully synthetic — no real patient data, no IRB concerns.
- Distributions are informed by MRI scheduling research conducted as part of
  dissertation work in Industrial & Systems Engineering at the University of Washington.
- Procedure template durations reflect typical clinical slot allocations.
- Patient-level factors (claustrophobia, age, pediatric status) introduce
  realistic duration variability.

**Adherence Definition**
- A exam is classified as *adherent* if it finishes within **±10 minutes** of
  its scheduled end time.
- This threshold is common in radiology operations literature.

**Train/Test Split**
- Temporal split: **2023 data for training**, **2024 data for testing**.
- This simulates real-world deployment where models are trained on historical
  data and evaluated on future performance.

**Scanner Delay Bias**
- Each scanner has a built-in delay bias (ranging from -2 to +4 minutes)
  to simulate real performance differences between machines and sites.

**Cascade Delays**
- When an exam runs long, subsequent exams on the same scanner that day
  inherit a portion of the delay — simulating the real-world cascade effect.
""")
