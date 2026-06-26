"""
Executive Overview Page
-----------------------
High-level KPIs and trends for hospital operations managers.
"""

import duckdb
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Executive Overview", page_icon="📊", layout="wide")

DB_PATH = "data/mri_ops.duckdb"

@st.cache_data
def load_data():
    con = duckdb.connect(DB_PATH, read_only=True)
    scanner_perf = con.execute("SELECT * FROM mart_daily_scanner_performance").fetchdf()
    proc_var     = con.execute("SELECT * FROM mart_procedure_variability").fetchdf()
    con.close()
    return scanner_perf, proc_var

scanner_perf, proc_var = load_data()

st.title("📊 Executive Overview")
st.caption("High-level MRI operations performance across all sites and scanners.")

# ── KPI Row ───────────────────────────────────────────────────────────────────
total_exams     = scanner_perf["total_exams"].sum()
overall_adh     = scanner_perf["adherent_exams"].sum() / total_exams * 100
avg_delay       = scanner_perf["avg_start_delay_min"].mean()
avg_duration    = scanner_perf["avg_actual_duration_min"].mean()
equipment_issues = scanner_perf["equipment_issues"].sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Exams",        f"{total_exams:,}")
col2.metric("Adherence Rate",     f"{overall_adh:.1f}%",  delta=f"{overall_adh - 50:.1f}% vs 50% target")
col3.metric("Avg Start Delay",    f"{avg_delay:.1f} min")
col4.metric("Avg Actual Duration",f"{avg_duration:.1f} min")
col5.metric("Equipment Issues",   f"{equipment_issues:,}")

st.divider()

# ── Adherence trend ───────────────────────────────────────────────────────────
st.subheader("Adherence Rate Over Time")

monthly = scanner_perf.copy()
monthly["exam_date"] = pd.to_datetime(monthly["exam_date"])
monthly["month"] = monthly["exam_date"].dt.to_period("M").astype(str)
monthly_agg = monthly.groupby("month").agg(
    adherent_exams=("adherent_exams", "sum"),
    total_exams=("total_exams", "sum")
).reset_index()
monthly_agg["adherence_rate_pct"] = monthly_agg["adherent_exams"] / monthly_agg["total_exams"] * 100

fig = px.line(
    monthly_agg, x="month", y="adherence_rate_pct",
    title="Monthly Schedule Adherence Rate (%)",
    labels={"month": "Month", "adherence_rate_pct": "Adherence Rate (%)"},
    markers=True,
)
fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50% target")
fig.update_layout(height=350)
st.plotly_chart(fig, use_container_width=True)

# ── Scanner comparison ────────────────────────────────────────────────────────
st.subheader("Scanner Performance Comparison")

scanner_summary = scanner_perf.groupby(["scanner_id", "site"]).agg(
    total_exams=("total_exams", "sum"),
    adherence_rate_pct=("adherent_exams", lambda x: x.sum() / scanner_perf.loc[x.index, "total_exams"].sum() * 100),
    avg_start_delay_min=("avg_start_delay_min", "mean"),
).reset_index().round(1)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        scanner_summary.sort_values("adherence_rate_pct"),
        x="adherence_rate_pct", y="scanner_id",
        orientation="h", color="site",
        title="Adherence Rate by Scanner (%)",
        labels={"adherence_rate_pct": "Adherence Rate (%)", "scanner_id": "Scanner"},
    )
    fig.add_vline(x=50, line_dash="dash", line_color="red")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        scanner_summary.sort_values("avg_start_delay_min", ascending=False),
        x="avg_start_delay_min", y="scanner_id",
        orientation="h", color="site",
        title="Avg Start Delay by Scanner (min)",
        labels={"avg_start_delay_min": "Avg Start Delay (min)", "scanner_id": "Scanner"},
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

# ── Procedure variability ─────────────────────────────────────────────────────
st.subheader("Top Procedures by Delay Contribution")

top_procs = proc_var.nlargest(10, "avg_duration_variance_min")[
    ["procedure_name", "complexity", "total_exams",
     "avg_duration_variance_min", "adherence_rate_pct", "p90_end_delta_min"]
].round(1)

st.dataframe(
    top_procs.rename(columns={
        "procedure_name": "Procedure",
        "complexity": "Complexity",
        "total_exams": "Total Exams",
        "avg_duration_variance_min": "Avg Duration Variance (min)",
        "adherence_rate_pct": "Adherence Rate (%)",
        "p90_end_delta_min": "P90 End Delta (min)",
    }),
    use_container_width=True,
    hide_index=True,
)
