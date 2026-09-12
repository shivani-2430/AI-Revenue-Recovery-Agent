import os
import joblib
import pandas as pd


# ============================================================
# MODEL PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "recovery_model.pkl"
)


# ============================================================
# LOAD MODEL
# ============================================================

_model = None


def load_model():
    global _model

    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "Recovery model not found. "
                "Run train_recovery_model.py first."
            )

        _model = joblib.load(MODEL_PATH)

    return _model


# ============================================================
# BATCH PREDICT RECOVERY
# ============================================================

def predict_recovery_batch(rows):
    if not rows:
        return []

    model = load_model()

    data = pd.DataFrame(rows)

    probabilities = model.predict_proba(data)[:, 1]

    results = []

    for probability in probabilities:
        probability = float(probability)

        prediction = int(probability >= 0.50)

        results.append({
            "recovery_probability": round(
                probability,
                4
            ),
            "recovery_percentage": round(
                probability * 100,
                2
            ),
            "prediction": (
                "RECOVERABLE"
                if prediction == 1
                else "NOT_RECOVERABLE"
            ),
        })

    return results


# ============================================================
# PREDICT RECOVERY
# ============================================================

def predict_recovery(
    amount,
    payment_method,
    merchant_category,
    failure_reason,
    retry_count,
    customer_segment,
    customer_age_days,
    successful_payments,
    failed_payments,
    historical_success_rate,
    customer_value,
    subscription_status,
    hour,
    day_of_week,
    high_value_customer,
    previous_recovery_success,
):

    row = {
        "amount": amount,
        "payment_method": payment_method,
        "merchant_category": merchant_category,
        "failure_reason": failure_reason,
        "retry_count": retry_count,
        "customer_segment": customer_segment,
        "customer_age_days": customer_age_days,
        "successful_payments": successful_payments,
        "failed_payments": failed_payments,
        "historical_success_rate": historical_success_rate,
        "customer_value": customer_value,
        "subscription_status": subscription_status,
        "hour": hour,
        "day_of_week": day_of_week,
        "high_value_customer": high_value_customer,
        "previous_recovery_success": previous_recovery_success,
    }

    return predict_recovery_batch([row])[0]


# ============================================================
# REVENUE AT RISK
# ============================================================

def calculate_revenue_at_risk(
    amount,
    recovery_probability,
):

    return round(
        float(amount)
        * float(recovery_probability),
        2,
    )