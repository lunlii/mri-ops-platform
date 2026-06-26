"""
Procedure & Scanner Performance Page
"""

import duckdb
import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Procedure & Scanner Performance", page_icon="🔬", layout="wide")

DB_PATH = "data/mri_ops.duckdb"

@st.cache_data
def load_data():
    con = duckdb.connect(DB_PATH, read_only=True)
    proc_var     = con.execute("SELECT * FROM mart_procedure_variability").fetchdf()
    scanner_perf = con.execute("SELECT * FROM mart_daily_scanner_performance").fetchdf()
    con.close()
    return proc_var, scanner_perf

proc_var, scanner_perf = load_data()

st.title("🔬 Procedure & Scanner Performance")

tab1, tab2 = st.tabs(["Procedures", "Scanners"])

# ── Procedures Tab ────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Procedure Duration Variability")

    complexity_filter = st.multiselect(
        "Filter by complexity", ["low", "medium", "high"],
        default=["low", "medium", "high"]
    )
    filtered = proc_var[proc_var["complexity"].isin(complexity_filter)]

    fig = px.scatter(
        filtered,
        x="avg_actual_duration_min",
        y="stddev_duration_min",
        size="total_exams",
        color="complexity",
        hover_name="procedure_name",
        title="Duration Variability: Mean vs Std Dev (bubble size = volume)",
        labels={
            "avg_actual_duration_min": "Avg Actual Duration (min)",
            "stddev_duration_min": "Std Dev Duration (min)",
        },
        color_discrete_map={"low": "#2ecc71", "medium": "#f39c12", "high": "#e74c3c"},
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Procedure Performance Table")
    st.dataframe(
        filtered[[
            "procedure_name", "complexity", "is_contrast", "total_exams",
            "template_duration_min", "avg_actual_duration_min",
            "stddev_duration_min", "avg_duration_variance_min",
            "adherence_rate_pct", "p90_duration_min"
        ]].sort_values("avg_duration_variance_min", ascending=False).round(1).rename(columns={
            "procedure_name": "Procedure",
            "complexity": "Complexity",
            "is_contrast": "Contrast",
            "total_exams": "Exams",
            "template_duration_min": "Template (min)",
            "avg_actual_duration_min": "Avg Actual (min)",
            "stddev_duration_min": "Std Dev (min)",
            "avg_duration_variance_min": "Variance (min)",
            "adherence_rate_pct": "Adherence (%)",
            "p90_duration_min": "P90 Duration (min)",
        }),
        use_container_width=True,
        hide_index=True,
    )

# ── Scanners Tab ──────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Scanner Utilization & Delay Trends")

    scanner_id = st.selectbox("Select Scanner", sorted(scanner_perf["scanner_id"].unique()))
    scanner_data = scanner_perf[scanner_perf["scanner_id"] == scanner_id].copy()
    scanner_data["exam_date"] = pd.to_datetime(scanner_data["exam_date"])
    scanner_data = scanner_data.sort_values("exam_date")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Exams",     f"{scanner_data['total_exams'].sum():,}")
    col2.metric("Avg Adherence",   f"{scanner_data['adherence_rate_pct'].mean():.1f}%")
    col3.metric("Avg Start Delay", f"{scanner_data['avg_start_delay_min'].mean():.1f} min")

    fig = px.line(
        scanner_data, x="exam_date", y="adherence_rate_pct",
        title=f"{scanner_id} — Daily Adherence Rate (%)",
        labels={"exam_date": "Date", "adherence_rate_pct": "Adherence Rate (%)"},
    )
    fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50% target")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.line(
        scanner_data, x="exam_date", y="avg_start_delay_min",
        title=f"{scanner_id} — Daily Avg Start Delay (min)",
        labels={"exam_date": "Date", "avg_start_delay_min": "Avg Start Delay (min)"},
        color_discrete_sequence=["#e74c3c"],
    )
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)
