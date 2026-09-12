#  Smart Failure Detection using Machine Learning

##  Project Overview

Smart Failure Detection using Machine Learning is an AI-powered web application developed as part of the **Infosys Springboard Internship Program**.

The application helps organizations, startup founders, entrepreneurs, and business analysts evaluate the potential risk associated with software projects before implementation.

The system collects project information, stores it securely in a PostgreSQL database, and applies a trained **Random Forest Machine Learning model** to predict the project's risk level (**Low, Medium, or High**). It further provides risk assessment, AI recommendations, market intelligence, AI decision simulation, and an executive report to support better business decisions.

---

#  Problem Statement

Many software projects fail because of poor planning, inadequate budgeting, unrealistic timelines, and ineffective resource allocation.

Organizations often struggle to identify project risks during the planning stage, leading to increased costs and project failures.

This project addresses these challenges by combining machine learning with project analytics to estimate project risk and provide actionable recommendations before execution.

---

#  Features

-  Project Registration
-  AI-Powered Risk Prediction
-  Random Forest Machine Learning Model
-  Risk Assessment Dashboard
-  AI Recommendations
-  Market Intelligence
-  AI Decision Simulator
-  Executive Report
-  PostgreSQL Database Integration
-  Responsive User Interface

---

#  Machine Learning Module

### Algorithm Used

- Random Forest Classifier

### Input Features

- Budget
- Team Size
- Timeline
- Priority
- Domain

### Output

- 🟢 Low Risk
- 🟡 Medium Risk
- 🔴 High Risk

### Libraries Used

- Scikit-learn
- Pandas
- NumPy
- Joblib

---

#  Technology Stack

| Category | Technology |
|----------|------------|
| Backend | Python, Flask |
| Frontend | HTML5, CSS3, JavaScript, Jinja2 |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Machine Learning | Random Forest |
| Data Processing | Pandas, NumPy |
| ML Utilities | Joblib |
| Report Generation | ReportLab |
| Icons | Font Awesome |
| Deployment | Render |

---

#  System Architecture

```text
                User
                  │
                  ▼
          HTML / CSS Frontend
                  │
                  ▼
            Flask Backend
                  │
      ┌───────────┴───────────┐
      ▼                       ▼
PostgreSQL Database     Random Forest Model
      │                       │
      └───────────┬───────────┘
                  ▼
          Risk Assessment
                  │
                  ▼
        AI Recommendations
                  │
                  ▼
       Market Intelligence
                  │
                  ▼
      AI Decision Simulator
                  │
                  ▼
          Executive Report
```

---

#  Project Workflow

1. User submits project details.
2. Project information is stored in PostgreSQL.
3. The Random Forest model predicts the project risk level.
4. Risk Assessment is generated.
5. AI Recommendations are provided.
6. Market Intelligence is displayed.
7. AI Decision Simulator evaluates different project scenarios.
8. Executive Report summarizes the complete analysis.

---

#  Project Structure

```text
Smart-Failure-Detection-ML
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
│
├── database/
├── models/
├── routes/
├── services/
├── static/
│
├── templates/
│
└── ml/
    ├── dataset.csv
    ├── train_model.py
    ├── predict.py
    ├── model.pkl
    ├── domain_encoder.pkl
    ├── priority_encoder.pkl
    └── risk_encoder.pkl
```

---

# ⚙ Installation

### Clone Repository

```bash
git clone <repository-url>
cd Smart-Failure-Detection-ML
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure PostgreSQL

Update the PostgreSQL connection details inside **config.py**.

### Run Application

```bash
python app.py
```

Open

```
http://127.0.0.1:5000
```

---

#  Application Modules

- Project Registration
- Risk Assessment
- AI Recommendations
- Market Intelligence
- AI Decision Simulator
- Executive Report

---

#  Machine Learning Workflow

```text
Project Details
        │
        ▼
Data Preprocessing
        │
        ▼
Feature Encoding
        │
        ▼
Random Forest Classifier
        │
        ▼
Risk Prediction
        │
        ▼
Low / Medium / High Risk
```

---

#  Target Users

- Startup Founders
- Entrepreneurs
- Business Analysts
- Investors
- Incubation Centers
- Project Managers

---

#  Future Enhancements

- Live Market Data Integration
- XGBoost-Based Risk Prediction
- Deep Learning Models
- User Authentication
- Docker Containerization
- Cloud-Based Model Retraining
- Interactive Analytics Dashboard
- REST API Integration

---

#  Developed By

**Shivani Tangudu**

B.Tech – Artificial Intelligence & Machine Learning

Infosys Springboard Internship Project

---

#  License

This project was developed for educational and internship purposes under the **Infosys Springboard Internship Program**.