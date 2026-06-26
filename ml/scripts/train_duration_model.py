"""
Exam Duration Prediction Model
-------------------------------
Predicts actual exam duration in minutes given procedure type,
scanner, time of day, and patient-level factors.

Features:
    - procedure_code (categorical)
    - complexity (categorical)
    - is_contrast (boolean)
    - template_duration_min (numeric)
    - day_of_week (categorical)
    - hour_of_day (numeric)
    - time_bucket (categorical)
    - scanner_id (categorical)
    - site (categorical)
    - field_strength (categorical)

Target: actual_duration_min

Models:
    - Baseline: template_duration_min (no ML)
    - Model: GradientBoostingRegressor

Metrics: MAE, RMSE, MAPE vs baseline
"""

import os
import json
import joblib
import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

# ── Config ───────────────────────────────────────────────────────────────────
DB_PATH      = "data/mri_ops.duckdb"
ARTIFACT_DIR = "ml/artifacts"
REPORT_DIR   = "ml/reports"
RANDOM_STATE = 42

os.makedirs(ARTIFACT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR,   exist_ok=True)

# ── Load features from dbt mart ───────────────────────────────────────────────
print("Loading features from mart_ml_features...")
con = duckdb.connect(DB_PATH)
df  = con.execute("SELECT * FROM mart_ml_features").fetchdf()
con.close()
print(f"  {len(df):,} rows loaded")

# ── Feature selection ─────────────────────────────────────────────────────────
CATEGORICAL_FEATURES = [
    "procedure_code", "complexity", "day_of_week",
    "time_bucket", "scanner_id", "site", "field_strength"
]
NUMERIC_FEATURES = [
    "template_duration_min", "hour_of_day"
]
BOOLEAN_FEATURES = ["is_contrast"]
TARGET = "actual_duration_min"

# Encode boolean as int
df["is_contrast"] = df["is_contrast"].astype(int)

feature_cols = CATEGORICAL_FEATURES + NUMERIC_FEATURES + BOOLEAN_FEATURES
X = df[feature_cols]
y = df[TARGET]

# ── Train / test split ────────────────────────────────────────────────────────
# Temporal split: train on 2023, test on 2024
train_mask = df["exam_date"].astype(str).str.startswith("2023")
X_train, X_test = X[train_mask],  X[~train_mask]
y_train, y_test = y[train_mask],  y[~train_mask]

print(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")

# ── Preprocessing pipeline ────────────────────────────────────────────────────
preprocessor = ColumnTransformer(transformers=[
    ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CATEGORICAL_FEATURES),
    ("num", StandardScaler(), NUMERIC_FEATURES + BOOLEAN_FEATURES),
])

model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("regressor", GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        random_state=RANDOM_STATE,
    ))
])

# ── Train ─────────────────────────────────────────────────────────────────────
print("\nTraining duration prediction model...")
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────
y_pred     = model.predict(X_test)
y_baseline = X_test["template_duration_min"].values

def mape(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

metrics = {
    "model": {
        "mae":  round(mean_absolute_error(y_test, y_pred), 2),
        "rmse": round(root_mean_squared_error(y_test, y_pred), 2),
        "mape": round(mape(y_test.values, y_pred), 2),
    },
    "baseline": {
        "mae":  round(mean_absolute_error(y_test, y_baseline), 2),
        "rmse": round(root_mean_squared_error(y_test, y_baseline), 2),
        "mape": round(mape(y_test.values, y_baseline), 2),
    },
    "train_size": len(X_train),
    "test_size":  len(X_test),
    "features":   feature_cols,
}

print("\nResults:")
print(f"  {'Metric':<8} {'Baseline':>10} {'Model':>10} {'Improvement':>12}")
print(f"  {'-'*42}")
for metric in ["mae", "rmse", "mape"]:
    base_val  = metrics["baseline"][metric]
    model_val = metrics["model"][metric]
    unit      = "%" if metric == "mape" else "min"
    improvement = ((base_val - model_val) / base_val) * 100
    print(f"  {metric.upper():<8} {base_val:>9.2f}{unit} {model_val:>9.2f}{unit} {improvement:>10.1f}%↓")

# ── Save ──────────────────────────────────────────────────────────────────────
joblib.dump(model, f"{ARTIFACT_DIR}/duration_model.pkl")
with open(f"{REPORT_DIR}/duration_model_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print(f"\nSaved model  → {ARTIFACT_DIR}/duration_model.pkl")
print(f"Saved report → {REPORT_DIR}/duration_model_metrics.json")
