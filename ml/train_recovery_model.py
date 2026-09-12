import os
import json
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "recovery_dataset.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "recovery_model.pkl"
)

METRICS_PATH = os.path.join(
    BASE_DIR,
    "model_metrics.json"
)


RANDOM_STATE = 42


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("AI REVENUE RECOVERY MODEL TRAINING")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_csv(DATASET_PATH)

print(f"Total transactions: {len(df):,}")


# ============================================================
# FILTER FAILED TRANSACTIONS
# ============================================================

failed_df = df[
    df["status"] == "FAILED"
].copy()

print(
    f"Failed transactions: {len(failed_df):,}"
)


# ============================================================
# CREATE REAL OUTCOME TARGET
# ============================================================

# A payment is considered recovered if the simulated
# recovery process actually recovered a positive amount.

failed_df["recovered"] = (
    failed_df["actual_recovery"] > 0
).astype(int)


print("\nTarget distribution:")

print(
    failed_df["recovered"]
    .value_counts()
    .rename(
        {
            0: "NOT_RECOVERED",
            1: "RECOVERED",
        }
    )
)


# ============================================================
# FEATURE SELECTION
# ============================================================

FEATURES = [
    "amount",
    "payment_method",
    "merchant_category",
    "failure_reason",
    "retry_count",
    "customer_segment",
    "customer_age_days",
    "successful_payments",
    "failed_payments",
    "historical_success_rate",
    "customer_value",
    "subscription_status",
    "hour",
    "day_of_week",
    "high_value_customer",
    "previous_recovery_success",
]


TARGET = "recovered"


X = failed_df[FEATURES].copy()

y = failed_df[TARGET].copy()


# ============================================================
# FEATURE TYPES
# ============================================================

NUMERIC_FEATURES = [
    "amount",
    "retry_count",
    "customer_age_days",
    "successful_payments",
    "failed_payments",
    "historical_success_rate",
    "customer_value",
    "hour",
    "day_of_week",
    "high_value_customer",
    "previous_recovery_success",
]

CATEGORICAL_FEATURES = [
    "payment_method",
    "merchant_category",
    "failure_reason",
    "customer_segment",
    "subscription_status",
]


# ============================================================
# PREPROCESSING
# ============================================================

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="median"
            ),
        )
    ]
)


categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="most_frequent"
            ),
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
        ),
    ]
)


preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_pipeline,
            NUMERIC_FEATURES,
        ),
        (
            "categorical",
            categorical_pipeline,
            CATEGORICAL_FEATURES,
        ),
    ]
)


# ============================================================
# MODEL
# ============================================================

model = RandomForestClassifier(
    n_estimators=350,
    max_depth=12,
    min_samples_split=8,
    min_samples_leaf=3,
    class_weight="balanced",
    random_state=RANDOM_STATE,
    n_jobs=-1,
)


pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor,
        ),
        (
            "model",
            model,
        ),
    ]
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=RANDOM_STATE,
    stratify=y,
)


print("\nDataset split:")
print(
    f"Training samples: {len(X_train):,}"
)
print(
    f"Testing samples:  {len(X_test):,}"
)


# ============================================================
# TRAIN
# ============================================================

print("\nTraining Random Forest...")

pipeline.fit(
    X_train,
    y_train,
)

print("Training complete.")


# ============================================================
# PREDICTION
# ============================================================

y_pred = pipeline.predict(
    X_test
)

y_probability = pipeline.predict_proba(
    X_test
)[:, 1]


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred,
)

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0,
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0,
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0,
)

roc_auc = roc_auc_score(
    y_test,
    y_probability,
)

matrix = confusion_matrix(
    y_test,
    y_pred,
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("MODEL PERFORMANCE")
print("=" * 70)

print(
    f"Accuracy:  {accuracy:.4f}"
)

print(
    f"Precision: {precision:.4f}"
)

print(
    f"Recall:    {recall:.4f}"
)

print(
    f"F1 Score:  {f1:.4f}"
)

print(
    f"ROC-AUC:   {roc_auc:.4f}"
)

print("\nConfusion Matrix:")

print(matrix)

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred,
        target_names=[
            "NOT_RECOVERED",
            "RECOVERED",
        ],
        zero_division=0,
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    pipeline,
    MODEL_PATH,
)


print(
    f"\nModel saved to:\n{MODEL_PATH}"
)


# ============================================================
# SAVE METRICS
# ============================================================

metrics = {
    "model": "RandomForestClassifier",
    "dataset_rows": int(len(df)),
    "failed_transactions": int(
        len(failed_df)
    ),
    "training_samples": int(
        len(X_train)
    ),
    "testing_samples": int(
        len(X_test)
    ),
    "features": FEATURES,
    "numeric_features": NUMERIC_FEATURES,
    "categorical_features": CATEGORICAL_FEATURES,
    "accuracy": round(
        float(accuracy),
        4,
    ),
    "precision": round(
        float(precision),
        4,
    ),
    "recall": round(
        float(recall),
        4,
    ),
    "f1_score": round(
        float(f1),
        4,
    ),
    "roc_auc": round(
        float(roc_auc),
        4,
    ),
    "confusion_matrix": matrix.tolist(),
}


with open(
    METRICS_PATH,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        metrics,
        file,
        indent=4,
    )


print(
    f"Metrics saved to:\n{METRICS_PATH}"
)

print("=" * 70)