"""
Schedule Adherence Classification Model
-----------------------------------------
Predicts whether an exam will finish within ±10 minutes of
its scheduled end time (adherent = True/False).

Features: same as duration model
Target: adherent (boolean → 0/1)

Model: GradientBoostingClassifier
Metrics: AUC-ROC, Precision, Recall, F1
"""

import os
import json
import joblib
import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report
)

# ── Config ───────────────────────────────────────────────────────────────────
DB_PATH      = "data/mri_ops.duckdb"
ARTIFACT_DIR = "ml/artifacts"
REPORT_DIR   = "ml/reports"
RANDOM_STATE = 42

os.makedirs(ARTIFACT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR,   exist_ok=True)

# ── Load features ─────────────────────────────────────────────────────────────
print("Loading features from mart_ml_features...")
con = duckdb.connect(DB_PATH)
df  = con.execute("SELECT * FROM mart_ml_features").fetchdf()
con.close()
print(f"  {len(df):,} rows loaded")
print(f"  Adherence rate: {df['adherent'].mean():.1%}")

# ── Features ──────────────────────────────────────────────────────────────────
CATEGORICAL_FEATURES = [
    "procedure_code", "complexity", "day_of_week",
    "time_bucket", "scanner_id", "site", "field_strength"
]
NUMERIC_FEATURES = ["template_duration_min", "hour_of_day"]
BOOLEAN_FEATURES = ["is_contrast"]
TARGET = "adherent"

df["is_contrast"] = df["is_contrast"].astype(int)
df[TARGET]        = df[TARGET].astype(int)

feature_cols = CATEGORICAL_FEATURES + NUMERIC_FEATURES + BOOLEAN_FEATURES
X = df[feature_cols]
y = df[TARGET]

# ── Temporal train/test split ─────────────────────────────────────────────────
train_mask = df["exam_date"].astype(str).str.startswith("2023")
X_train, X_test = X[train_mask],  X[~train_mask]
y_train, y_test = y[train_mask],  y[~train_mask]

print(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")

# ── Pipeline ──────────────────────────────────────────────────────────────────
preprocessor = ColumnTransformer(transformers=[
    ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CATEGORICAL_FEATURES),
    ("num", StandardScaler(), NUMERIC_FEATURES + BOOLEAN_FEATURES),
])

model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=RANDOM_STATE,
    ))
])

# ── Train ─────────────────────────────────────────────────────────────────────
print("\nTraining schedule adherence classification model...")
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────
y_pred      = model.predict(X_test)
y_prob      = model.predict_proba(X_test)[:, 1]

auc       = roc_auc_score(y_test, y_prob)
precision = precision_score(y_test, y_pred)
recall    = recall_score(y_test, y_pred)
f1        = f1_score(y_test, y_pred)
cm        = confusion_matrix(y_test, y_pred).tolist()

# Baseline: always predict majority class
baseline_pred = np.ones(len(y_test)) * y_train.mode()[0]
baseline_f1   = f1_score(y_test, baseline_pred)

metrics = {
    "model": {
        "auc_roc":   round(auc, 4),
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
    },
    "baseline": {
        "f1": round(baseline_f1, 4),
        "strategy": "majority class"
    },
    "confusion_matrix": cm,
    "train_size": len(X_train),
    "test_size":  len(X_test),
    "features":   feature_cols,
    "adherence_rate_train": round(y_train.mean(), 4),
    "adherence_rate_test":  round(y_test.mean(), 4),
}

print("\nResults:")
print(f"  AUC-ROC  : {auc:.4f}")
print(f"  Precision: {precision:.4f}")
print(f"  Recall   : {recall:.4f}")
print(f"  F1       : {f1:.4f}  (baseline: {baseline_f1:.4f})")
print(f"\nConfusion Matrix:")
print(f"  TN={cm[0][0]:,}  FP={cm[0][1]:,}")
print(f"  FN={cm[1][0]:,}  TP={cm[1][1]:,}")

# ── Save ──────────────────────────────────────────────────────────────────────
joblib.dump(model, f"{ARTIFACT_DIR}/adherence_model.pkl")
with open(f"{REPORT_DIR}/adherence_model_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print(f"\nSaved model  → {ARTIFACT_DIR}/adherence_model.pkl")
print(f"Saved report → {REPORT_DIR}/adherence_model_metrics.json")
