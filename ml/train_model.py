import pandas as pd
import joblib

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load Dataset
df = pd.read_csv("ml/dataset.csv")

print(df.head())

# -------------------------
# Encode Categorical Columns
# -------------------------

domain_encoder = LabelEncoder()
priority_encoder = LabelEncoder()
risk_encoder = LabelEncoder()

df["Domain"] = domain_encoder.fit_transform(df["Domain"])
df["Priority"] = priority_encoder.fit_transform(df["Priority"])
df["Risk"] = risk_encoder.fit_transform(df["Risk"])

# -------------------------
# Features
# -------------------------

X = df[[
    "Budget",
    "Team_Size",
    "Timeline",
    "Priority",
    "Domain"
]]

y = df["Risk"]

# -------------------------
# Split Dataset
# -------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# -------------------------
# Train Random Forest
# -------------------------

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# -------------------------
# Prediction
# -------------------------

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("\nAccuracy :", accuracy)

# -------------------------
# Save Everything
# -------------------------

joblib.dump(model, "ml/model.pkl")
joblib.dump(domain_encoder, "ml/domain_encoder.pkl")
joblib.dump(priority_encoder, "ml/priority_encoder.pkl")
joblib.dump(risk_encoder, "ml/risk_encoder.pkl")

print("\nModel Saved Successfully!")
