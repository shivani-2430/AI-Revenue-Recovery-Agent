import joblib
import pandas as pd


# =========================================================
# LOAD MODEL
# =========================================================

model = joblib.load("ml/model.pkl")


# =========================================================
# LOAD ENCODERS
# =========================================================

domain_encoder = joblib.load("ml/domain_encoder.pkl")
priority_encoder = joblib.load("ml/priority_encoder.pkl")
risk_encoder = joblib.load("ml/risk_encoder.pkl")


# =========================================================
# PREPARE PROJECT DATA
# =========================================================

def prepare_input(
    domain,
    budget,
    team_size,
    timeline,
    priority
):

    domain = domain.strip().title()
    priority = priority.strip().title()

    data = pd.DataFrame([{
        "Budget": float(budget),
        "Team_Size": int(team_size),
        "Timeline": int(timeline),
        "Priority": priority_encoder.transform(
            [priority]
        )[0],
        "Domain": domain_encoder.transform(
            [domain]
        )[0]
    }])

    return data


# =========================================================
# EXISTING RISK PREDICTION
# =========================================================

def predict_risk(
    domain,
    budget,
    team_size,
    timeline,
    priority
):

    data = prepare_input(
        domain,
        budget,
        team_size,
        timeline,
        priority
    )

    prediction = model.predict(data)

    return risk_encoder.inverse_transform(
        prediction
    )[0]


# =========================================================
# RISK PREDICTION + CONFIDENCE
# =========================================================

def predict_risk_with_confidence(
    domain,
    budget,
    team_size,
    timeline,
    priority
):

    data = prepare_input(
        domain,
        budget,
        team_size,
        timeline,
        priority
    )

    prediction = model.predict(data)

    risk_prediction = risk_encoder.inverse_transform(
        prediction
    )[0]

    # -----------------------------------------------------
    # Get probability for the predicted class
    # -----------------------------------------------------

    if hasattr(model, "predict_proba"):

        probabilities = model.predict_proba(data)[0]

        predicted_class_index = list(
            model.classes_
        ).index(prediction[0])

        confidence = (
            probabilities[predicted_class_index]
            * 100
        )

    else:

        # Model does not expose probability estimates.
        confidence = None

    return {
        "prediction": risk_prediction,
        "confidence": (
            round(confidence, 2)
            if confidence is not None
            else None
        )
    }