import os
import sys
from decimal import Decimal
from datetime import datetime

import pandas as pd

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from app import app
from database.db import db

from models import (
    Customer,
    Transaction,
    PaymentAttempt,
    RecoveryAction,
    RecoveryOutcome,
    AuditLog,
)

from ml.predict_recovery import (
    predict_recovery,
    calculate_revenue_at_risk,
)


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


# ============================================================
# HELPERS
# ============================================================

def parse_timestamp(value):
    return datetime.fromisoformat(
        str(value)
    )


def decimal_value(value):
    return Decimal(
        str(round(float(value), 2))
    )


def create_customer(customer_data):

    customer = Customer.query.filter_by(
        customer_id=customer_data["customer_id"]
    ).first()

    if customer:
        return customer

    customer = Customer(
        customer_id=customer_data["customer_id"],
        customer_segment=customer_data["customer_segment"],
        customer_since=datetime.utcnow(),
        successful_payments=int(
            customer_data["successful_payments"]
        ),
        failed_payments=int(
            customer_data["failed_payments"]
        ),
        historical_success_rate=float(
            customer_data[
                "historical_success_rate"
            ]
        ),
        customer_value=decimal_value(
            customer_data["customer_value"]
        ),
    )

    db.session.add(customer)

    return customer


# ============================================================
# SEED DATABASE
# ============================================================

def seed_database():

    print("=" * 70)
    print("AI REVENUE RECOVERY DATABASE SEEDER")
    print("=" * 70)

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    df = pd.read_csv(
        DATASET_PATH
    )

    print(
        f"\nDataset rows: {len(df):,}"
    )

    # --------------------------------------------------------
    # Limit initial database load
    # --------------------------------------------------------

    # 2,500 transactions gives us a realistic development
    # database without making local startup unnecessarily heavy.
    seed_df = df.head(2500).copy()

    print(
        f"Rows selected for database: "
        f"{len(seed_df):,}"
    )

    customers_created = 0
    transactions_created = 0
    attempts_created = 0
    actions_created = 0
    outcomes_created = 0
    audit_logs_created = 0

    customer_cache = {}

    # --------------------------------------------------------
    # Process transactions
    # --------------------------------------------------------

    for index, row in seed_df.iterrows():

        transaction_id = row[
            "transaction_id"
        ]

        # --------------------------------------------
        # Skip existing transaction
        # --------------------------------------------

        existing_transaction = (
            Transaction.query.filter_by(
                transaction_id=transaction_id
            ).first()
        )

        if existing_transaction:
            continue

        # --------------------------------------------
        # Customer
        # --------------------------------------------

        customer_id = row[
            "customer_id"
        ]

        if customer_id in customer_cache:

            customer = customer_cache[
                customer_id
            ]

        else:

            customer = create_customer(
                row
            )

            db.session.flush()

            customer_cache[
                customer_id
            ] = customer

            customers_created += 1

        # --------------------------------------------
        # Transaction
        # --------------------------------------------

        transaction = Transaction(
            transaction_id=transaction_id,
            customer_id=customer.id,
            amount=decimal_value(
                row["amount"]
            ),
            payment_method=row[
                "payment_method"
            ],
            merchant_category=row[
                "merchant_category"
            ],
            status=row[
                "status"
            ],
            failure_reason=(
                None
                if pd.isna(
                    row["failure_reason"]
                )
                else row["failure_reason"]
            ),
            transaction_timestamp=parse_timestamp(
                row["transaction_timestamp"]
            ),
            subscription_status=row[
                "subscription_status"
            ],
            retry_count=int(
                row["retry_count"]
            ),
        )

        db.session.add(
            transaction
        )

        db.session.flush()

        transactions_created += 1

        # --------------------------------------------
        # Payment attempts
        # --------------------------------------------

        total_attempts = max(
            1,
            int(row["retry_count"]) + 1
        )

        for attempt_number in range(
            1,
            total_attempts + 1
        ):

            is_final_attempt = (
                attempt_number
                == total_attempts
            )

            if row["status"] == "SUCCESS":

                attempt_status = "SUCCESS"

                attempt_failure_reason = None

                response_code = "SUCCESS"

            else:

                if is_final_attempt:

                    attempt_status = "FAILED"

                    attempt_failure_reason = (
                        None
                        if pd.isna(
                            row["failure_reason"]
                        )
                        else row[
                            "failure_reason"
                        ]
                    )

                    response_code = row[
                        "response_code"
                    ]

                else:

                    attempt_status = "FAILED"

                    attempt_failure_reason = (
                        None
                        if pd.isna(
                            row["failure_reason"]
                        )
                        else row[
                            "failure_reason"
                        ]
                    )

                    response_code = row[
                        "response_code"
                    ]

            attempt = PaymentAttempt(
                transaction_id=transaction.id,
                attempt_number=attempt_number,
                attempted_at=parse_timestamp(
                    row[
                        "transaction_timestamp"
                    ]
                ),
                status=attempt_status,
                failure_reason=attempt_failure_reason,
                response_code=response_code,
            )

            db.session.add(
                attempt
            )

            attempts_created += 1

        # --------------------------------------------
        # ML recovery decision
        # --------------------------------------------

        if row["status"] != "FAILED":
            continue

        prediction = predict_recovery(
            amount=float(
                row["amount"]
            ),
            payment_method=row[
                "payment_method"
            ],
            merchant_category=row[
                "merchant_category"
            ],
            failure_reason=row[
                "failure_reason"
            ],
            retry_count=int(
                row["retry_count"]
            ),
            customer_segment=row[
                "customer_segment"
            ],
            customer_age_days=int(
                row["customer_age_days"]
            ),
            successful_payments=int(
                row["successful_payments"]
            ),
            failed_payments=int(
                row["failed_payments"]
            ),
            historical_success_rate=float(
                row[
                    "historical_success_rate"
                ]
            ),
            customer_value=float(
                row["customer_value"]
            ),
            subscription_status=row[
                "subscription_status"
            ],
            hour=int(
                row["hour"]
            ),
            day_of_week=int(
                row["day_of_week"]
            ),
            high_value_customer=int(
                row[
                    "high_value_customer"
                ]
            ),
            previous_recovery_success=int(
                row[
                    "previous_recovery_success"
                ]
            ),
        )

        recovery_probability = prediction[
            "recovery_probability"
        ]

        recovery_percentage = prediction[
            "recovery_percentage"
        ]

        prediction_label = prediction[
            "prediction"
        ]

        revenue_at_risk = (
            calculate_revenue_at_risk(
                float(row["amount"]),
                recovery_probability,
            )
        )

        # --------------------------------------------
        # Determine recovery action
        # --------------------------------------------

        failure_reason = row[
            "failure_reason"
        ]

        retry_count = int(
            row["retry_count"]
        )

        if recovery_probability < 0.25:

            action_type = "ESCALATE"

            reason = (
                "ML model indicates low "
                "recovery probability. "
                "Automated intervention is "
                "not recommended."
            )

        elif failure_reason in [
            "NETWORK_ERROR",
            "GATEWAY_TIMEOUT",
        ]:

            if retry_count < 2:

                action_type = "SMART_RETRY"

                reason = (
                    "Transient payment failure "
                    "with remaining retry capacity."
                )

            else:

                action_type = (
                    "CUSTOMER_NOTIFICATION"
                )

                reason = (
                    "Transient failure has "
                    "reached the retry threshold."
                )

        elif failure_reason in [
            "EXPIRED_CARD",
            "AUTHENTICATION_FAILED",
            "LIMIT_EXCEEDED",
        ]:

            action_type = "PAYMENT_LINK"

            reason = (
                "Payment requires customer "
                "intervention before another "
                "attempt."
            )

        elif failure_reason == (
            "INSUFFICIENT_FUNDS"
        ):

            action_type = (
                "CUSTOMER_NOTIFICATION"
            )

            reason = (
                "Customer notification can "
                "prompt a new payment attempt."
            )

        elif failure_reason == (
            "MANDATE_FAILURE"
        ):

            action_type = "MANDATE_RETRY"

            reason = (
                "Mandate failure may be "
                "recoverable through a "
                "controlled retry."
            )

        elif failure_reason == (
            "BANK_DECLINE"
        ):

            if retry_count < 1:

                action_type = "SMART_RETRY"

                reason = (
                    "Bank decline with available "
                    "retry capacity."
                )

            else:

                action_type = (
                    "CUSTOMER_NOTIFICATION"
                )

                reason = (
                    "Repeated bank decline "
                    "requires customer intervention."
                )

        else:

            action_type = (
                "CUSTOMER_NOTIFICATION"
            )

            reason = (
                "Payment failure requires "
                "controlled customer intervention."
            )

        # --------------------------------------------
        # Recovery Action
        # --------------------------------------------

        guardrail_status = "PASSED"

        if retry_count >= 3:
            guardrail_status = "BLOCKED"

        if action_type == "SMART_RETRY" and (
            retry_count >= 3
        ):
            guardrail_status = "BLOCKED"

        action_status = (
            "RECOMMENDED"
            if prediction_label
            == "RECOVERABLE"
            else "ESCALATED"
        )

        recovery_action = RecoveryAction(
            transaction_id=transaction.id,
            action_type=action_type,
            reason=(
                f"{reason} "
                f"Model recovery probability: "
                f"{recovery_percentage:.2f}%."
            ),
            risk_score=round(
                100 - (
                    recovery_probability
                    * 100
                ),
                2,
            ),
            recovery_probability=(
                recovery_probability
            ),
            revenue_at_risk=decimal_value(
                revenue_at_risk
            ),
            status=action_status,
            guardrail_status=guardrail_status,
        )

        db.session.add(
            recovery_action
        )

        db.session.flush()

        actions_created += 1

        # --------------------------------------------
        # Recovery outcome
        # --------------------------------------------

        actual_recovery = float(
            row["actual_recovery"]
        )

        if actual_recovery > 0:

            outcome_value = "RECOVERED"

        else:

            outcome_value = "NOT_RECOVERED"

        recovery_outcome = RecoveryOutcome(
            transaction_id=transaction.id,
            recovery_action_id=recovery_action.id,
            outcome=outcome_value,
            amount_recovered=decimal_value(
                actual_recovery
            ),
        )

        db.session.add(
            recovery_outcome
        )

        outcomes_created += 1

        # --------------------------------------------
        # Audit trail
        # --------------------------------------------

        decision_id = (
            f"DEC_{transaction_id}"
        )

        audit_log = AuditLog(
            transaction_id=transaction.id,
            decision_id=decision_id,
            decision=prediction_label,
            reason=(
                f"ML recovery probability "
                f"{recovery_percentage:.2f}% "
                f"for failed payment."
            ),
            policy_check=guardrail_status,
            action=action_type,
            result=outcome_value,
            model_version="recovery-rf-v1",
        )

        db.session.add(
            audit_log
        )

        audit_logs_created += 1

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    db.session.commit()

    print("\n" + "=" * 70)
    print("DATABASE SEED COMPLETE")
    print("=" * 70)

    print(
        f"Customers created:        {customers_created:,}"
    )

    print(
        f"Transactions created:     {transactions_created:,}"
    )

    print(
        f"Payment attempts created: {attempts_created:,}"
    )

    print(
        f"Recovery actions created: {actions_created:,}"
    )

    print(
        f"Recovery outcomes:        {outcomes_created:,}"
    )

    print(
        f"Audit logs created:       {audit_logs_created:,}"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

        seed_database()