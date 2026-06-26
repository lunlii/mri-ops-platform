"""
Model Performance Page
"""

import json
import joblib
import duckdb
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import shap

st.set_page_config(page_title="Model Performance", page_icon="🤖", layout="wide")

DB_PATH      = "data/mri_ops.duckdb"
ARTIFACT_DIR = "ml/artifacts"
REPORT_DIR   = "ml/reports"

@st.cache_data
def load_metrics():
    with open(f"{REPORT_DIR}/duration_model_metrics.json") as f:
        duration = json.load(f)
    with open(f"{REPORT_DIR}/adherence_model_metrics.json") as f:
        adherence = json.load(f)
    return duration, adherence

@st.cache_data
def load_predictions():
    con = duckdb.connect(DB_PATH, read_only=True)
    df  = con.execute("SELECT * FROM mart_ml_features").fetchdf()
    con.close()

    duration_model  = joblib.load(f"{ARTIFACT_DIR}/duration_model.pkl")
    adherence_model = joblib.load(f"{ARTIFACT_DIR}/adherence_model.pkl")

    feature_cols = [
        "procedure_code", "complexity", "day_of_week", "time_bucket",
        "scanner_id", "site", "field_strength",
        "template_duration_min", "hour_of_day", "is_contrast"
    ]
    df["is_contrast"] = df["is_contrast"].astype(int)

    test_mask = df["exam_date"].astype(str).str.startswith("2024")
    df_test   = df[test_mask].copy()

    df_test["predicted_duration"]  = duration_model.predict(df_test[feature_cols])
    df_test["predicted_adherent"]  = adherence_model.predict(df_test[feature_cols])
    df_test["adherence_prob"]      = adherence_model.predict_proba(df_test[feature_cols])[:, 1]

    return df_test

@st.cache_resource
def load_models():
    duration_model  = joblib.load(f"{ARTIFACT_DIR}/duration_model.pkl")
    adherence_model = joblib.load(f"{ARTIFACT_DIR}/adherence_model.pkl")
    return duration_model, adherence_model

duration_metrics, adherence_metrics = load_metrics()
df_test = load_predictions()
duration_model, adherence_model = load_models()

st.title("🤖 Model Performance")
st.caption("Evaluation of the two ML models on held-out 2024 test data.")

tab1, tab2 = st.tabs(["Duration Prediction", "Adherence Classification"])

# ── Duration Model ────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Exam Duration Prediction — GradientBoostingRegressor")
    st.markdown("Predicts actual exam duration in minutes. Evaluated against template baseline.")

    col1, col2, col3 = st.columns(3)
    m = duration_metrics
    m = duration_metrics
    col1.metric("Model MAE",  f"{m['model']['mae']:.2f} min",  delta=f"{((m['baseline']['mae']-m['model']['mae'])/m['baseline']['mae']*100):.1f}% improvement over baseline", delta_color="normal")
    col2.metric("Model RMSE", f"{m['model']['rmse']:.2f} min", delta=f"{((m['baseline']['rmse']-m['model']['rmse'])/m['baseline']['rmse']*100):.1f}% improvement over baseline", delta_color="normal")
    col3.metric("Model MAPE", f"{m['model']['mape']:.2f}%",   delta=f"{((m['baseline']['mape']-m['model']['mape'])/m['baseline']['mape']*100):.1f}% improvement over baseline", delta_color="normal")
    st.subheader("Actual vs Predicted Duration")
    sample = df_test.sample(2000, random_state=42)
    fig = px.scatter(
        sample, x="actual_duration_min", y="predicted_duration",
        color="complexity", opacity=0.5,
        title="Actual vs Predicted Duration (2024 test set, n=2,000 sample)",
        labels={"actual_duration_min": "Actual Duration (min)", "predicted_duration": "Predicted Duration (min)"},
        color_discrete_map={"low": "#2ecc71", "medium": "#f39c12", "high": "#e74c3c"},
    )
    fig.add_shape(type="line", x0=0, y0=0, x1=200, y1=200, line=dict(dash="dash", color="gray"))
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Residuals by Procedure Complexity")
    df_test["residual"] = df_test["actual_duration_min"] - df_test["predicted_duration"]
    fig2 = px.box(
        df_test, x="complexity", y="residual",
        title="Prediction Residuals by Complexity (actual - predicted)",
        labels={"complexity": "Complexity", "residual": "Residual (min)"},
        color="complexity",
        color_discrete_map={"low": "#2ecc71", "medium": "#f39c12", "high": "#e74c3c"},
    )
    fig2.add_hline(y=0, line_dash="dash", line_color="gray")
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Feature Importance (SHAP)")
with st.spinner("Computing SHAP values (this may take a moment)..."):
    feature_cols = [
            "procedure_code", "complexity", "day_of_week", "time_bucket",
            "scanner_id", "site", "field_strength",
            "template_duration_min", "hour_of_day", "is_contrast"
    ]
    sample_100 = df_test.sample(100, random_state=42)
    X_sample = sample_100[feature_cols].copy()
    X_sample["is_contrast"] = X_sample["is_contrast"].astype(int)

    X_transformed = duration_model.named_steps["preprocessor"].transform(X_sample)

    explainer = shap.TreeExplainer(duration_model.named_steps["regressor"])
    shap_values = explainer.shap_values(X_transformed)

    shap_df = pd.DataFrame({
        "Feature": feature_cols,
        "Mean |SHAP|": abs(shap_values).mean(axis=0)
    }).sort_values("Mean |SHAP|", ascending=True)

    fig3 = px.bar(
        shap_df,
        x="Mean |SHAP|",
        y="Feature",
        orientation="h",
        title="Feature Importance — Mean Absolute SHAP Value (Duration Model)",
        labels={"Mean |SHAP|": "Mean |SHAP Value| (minutes)", "Feature": ""},
        color="Mean |SHAP|",
        color_continuous_scale="Blues",
    )
    fig3.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("SHAP values show the average impact of each feature on predicted exam duration. Higher = more influential.")

# ── Adherence Model ───────────────────────────────────────────────────────────
with tab2:
    st.subheader("Schedule Adherence Classification — GradientBoostingClassifier")
    st.markdown("Predicts whether an exam will finish within ±10 minutes of scheduled end.")

    m = adherence_metrics["model"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("AUC-ROC",   f"{m['auc_roc']:.4f}")
    col2.metric("Precision", f"{m['precision']:.4f}")
    col3.metric("Recall",    f"{m['recall']:.4f}")
    col4.metric("F1 Score",  f"{m['f1']:.4f}", delta=f"+{m['f1'] - adherence_metrics['baseline']['f1']:.4f} vs baseline")

    st.subheader("Adherence Probability Distribution")
    fig = px.histogram(
        df_test, x="adherence_prob", color="adherent",
        nbins=50, barmode="overlay", opacity=0.7,
        title="Predicted Adherence Probability by True Label",
        labels={"adherence_prob": "Predicted Probability (Adherent)", "adherent": "Actually Adherent"},
        color_discrete_map={True: "#2ecc71", False: "#e74c3c"},
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Confusion Matrix")
    cm = adherence_metrics["confusion_matrix"]
    cm_df = pd.DataFrame(cm,
        index=["Actually Non-Adherent", "Actually Adherent"],
        columns=["Predicted Non-Adherent", "Predicted Adherent"]
    )
    fig2 = px.imshow(
        cm_df, text_auto=True, color_continuous_scale="Blues",
        title="Confusion Matrix (2024 test set)",
    )
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)
