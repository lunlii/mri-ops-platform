"""
AI Assistant Page
-----------------
Natural language -> SQL -> result -> plain-English summary
Powered by Anthropic Claude via text-to-SQL over dbt marts.
"""

import os
import duckdb
import streamlit as st
import anthropic
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Assistant", page_icon="💬", layout="wide")

DB_PATH = "data/mri_ops.duckdb"

# ── Mart schema exposed to the LLM ────────────────────────────────────────────
MART_SCHEMA = """
You have access to three analytics tables in DuckDB. Generate SQL queries against these tables only.

TABLE: mart_daily_scanner_performance
  exam_date DATE
  scanner_id VARCHAR         -- e.g. SC01, SC02, SC07
  site VARCHAR               -- Main, North, South
  field_strength VARCHAR     -- 1.5T or 3.0T
  total_exams INTEGER
  adherent_exams INTEGER
  adherence_rate_pct FLOAT   -- % of exams finishing within ±10 min of scheduled end
  avg_actual_duration_min FLOAT
  avg_template_duration_min FLOAT
  avg_start_delay_min FLOAT
  avg_end_delta_min FLOAT
  stddev_duration_min FLOAT
  max_start_delay_min FLOAT
  equipment_issues INTEGER
  patient_late_count INTEGER
  high_delay_risk_count INTEGER

TABLE: mart_procedure_variability
  procedure_code VARCHAR
  procedure_name VARCHAR
  complexity VARCHAR          -- low, medium, high
  is_contrast BOOLEAN
  total_exams INTEGER
  template_duration_min FLOAT
  avg_actual_duration_min FLOAT
  stddev_duration_min FLOAT
  avg_duration_variance_min FLOAT   -- avg actual - avg template
  adherence_rate_pct FLOAT
  avg_start_delay_min FLOAT
  p90_duration_min FLOAT
  p90_end_delta_min FLOAT
  exams_over_template INTEGER
  exams_under_template INTEGER

TABLE: mart_ml_features
  appointment_id VARCHAR
  exam_date DATE
  actual_duration_min FLOAT
  adherent BOOLEAN
  procedure_code VARCHAR
  complexity VARCHAR
  is_contrast BOOLEAN
  template_duration_min FLOAT
  day_of_week VARCHAR
  hour_of_day INTEGER
  day_of_week_num INTEGER
  time_bucket VARCHAR         -- early_am, mid_am, early_pm, late_pm
  scanner_id VARCHAR
  site VARCHAR
  field_strength VARCHAR
  start_delay_min FLOAT
  delay_reason VARCHAR
  start_delay_risk VARCHAR    -- low, medium, high

Rules:
- Only query these three tables
- Use DuckDB SQL syntax
- Return only the SQL query, no explanation, no markdown fences
- For date filtering use: WHERE exam_date >= DATE '2024-01-01'
- For aggregations always include ORDER BY
- Limit results to 20 rows unless the user asks for more
"""

SYSTEM_PROMPT = f"""You are an MRI operations analytics assistant. 
Your job is to answer operational questions by generating SQL queries against a set of curated analytics tables.

{MART_SCHEMA}

When given a question:
1. Generate a single valid DuckDB SQL query
2. Return ONLY the SQL — no explanation, no backticks, no markdown
"""

SUMMARY_PROMPT = """You are an MRI operations analyst. 
Given a SQL query and its results, provide a concise 2-3 sentence plain-English summary 
of the key findings. Be specific — mention actual numbers from the results.
Focus on what an operations manager would care about."""

# ── Example questions ─────────────────────────────────────────────────────────
EXAMPLE_QUESTIONS = [
    "Which scanner had the lowest adherence rate overall?",
    "Which procedures caused the most delays on average?",
    "What is the adherence rate by day of week?",
    "Which site has the highest average start delay?",
    "What are the top 5 procedures by duration variability?",
    "How does adherence rate compare between 1.5T and 3.0T scanners?",
    "Which delay reason is most common?",
    "What is the average exam duration by complexity level?",
]

st.title("💬 AI Assistant")
st.caption("Ask operational questions in plain English. Claude generates SQL, runs it against the analytics marts, and summarizes the results.")

# ── Init chat history ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Example questions ─────────────────────────────────────────────────────────
st.subheader("Example Questions")
cols = st.columns(4)
for i, q in enumerate(EXAMPLE_QUESTIONS):
    if cols[i % 4].button(q, key=f"example_{i}"):
        st.session_state["prefill"] = q

# ── Chat interface ────────────────────────────────────────────────────────────
st.divider()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "df" in message:
            st.dataframe(message["df"], use_container_width=True, hide_index=True)
        if "sql" in message:
            with st.expander("Generated SQL"):
                st.code(message["sql"], language="sql")

# ── Input ─────────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")
user_input = st.chat_input("Ask a question about MRI operations...") or prefill

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Generating SQL..."):
            try:
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    st.error("ANTHROPIC_API_KEY not set. Add it to your .env file.")
                    st.stop()

                client = anthropic.Anthropic(api_key=api_key)

                # Step 1: Generate SQL
                sql_response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=500,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_input}],
                )
                sql = sql_response.content[0].text.strip()

                # Step 2: Execute SQL
                con = duckdb.connect(DB_PATH, read_only=True)
                df  = con.execute(sql).fetchdf()
                con.close()

                # Step 3: Summarize results
                summary_response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=300,
                    system=SUMMARY_PROMPT,
                    messages=[{
                        "role": "user",
                        "content": f"Question: {user_input}\n\nSQL: {sql}\n\nResults (first 5 rows):\n{df.head().to_string()}"
                    }],
                )
                summary = summary_response.content[0].text.strip()

                st.markdown(summary)
                st.dataframe(df, use_container_width=True, hide_index=True)
                with st.expander("Generated SQL"):
                    st.code(sql, language="sql")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": summary,
                    "df": df,
                    "sql": sql,
                })

            except duckdb.Error as e:
                error_msg = f"SQL error: {e}\n\nGenerated SQL:\n```sql\n{sql}\n```"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                st.error(f"Error: {e}")
