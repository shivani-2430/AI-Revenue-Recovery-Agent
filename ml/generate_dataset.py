import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42
NUM_TRANSACTIONS = 10000

random.seed(SEED)
np.random.seed(SEED)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "recovery_dataset.csv"
)


# ============================================================
# REFERENCE DATA
# ============================================================

PAYMENT_METHODS = [
    "CARD",
    "UPI",
    "NETBANKING",
    "WALLET",
    "EMANDATE",
]

MERCHANT_CATEGORIES = [
    "SaaS",
    "Ecommerce",
    "Education",
    "Healthcare",
    "Travel",
    "Entertainment",
    "Financial Services",
]

CUSTOMER_SEGMENTS = [
    "NEW",
    "STANDARD",
    "LOYAL",
    "HIGH_VALUE",
]

SUBSCRIPTION_STATUSES = [
    "ACTIVE",
    "TRIAL",
    "PAST_DUE",
    "CANCELLED",
]

FAILURE_REASONS = [
    "NETWORK_ERROR",
    "BANK_DECLINE",
    "INSUFFICIENT_FUNDS",
    "AUTHENTICATION_FAILED",
    "LIMIT_EXCEEDED",
    "EXPIRED_CARD",
    "MANDATE_FAILURE",
    "GATEWAY_TIMEOUT",
]

RESPONSE_CODES = {
    "NETWORK_ERROR": "NET_001",
    "BANK_DECLINE": "BANK_051",
    "INSUFFICIENT_FUNDS": "BANK_116",
    "AUTHENTICATION_FAILED": "AUTH_001",
    "LIMIT_EXCEEDED": "BANK_121",
    "EXPIRED_CARD": "CARD_012",
    "MANDATE_FAILURE": "MANDATE_001",
    "GATEWAY_TIMEOUT": "NET_504",
}


# ============================================================
# CUSTOMER GENERATION
# ============================================================

def generate_customer(customer_number):
    segment = random.choices(
        CUSTOMER_SEGMENTS,
        weights=[15, 50, 25, 10],
        k=1,
    )[0]

    if segment == "NEW":
        customer_age_days = random.randint(1, 90)
        successful_payments = random.randint(0, 5)
        failed_payments = random.randint(0, 3)
        customer_value = round(
            random.uniform(500, 15000),
            2,
        )

    elif segment == "STANDARD":
        customer_age_days = random.randint(91, 720)
        successful_payments = random.randint(3, 35)
        failed_payments = random.randint(0, 8)
        customer_value = round(
            random.uniform(5000, 50000),
            2,
        )

    elif segment == "LOYAL":
        customer_age_days = random.randint(365, 1800)
        successful_payments = random.randint(20, 100)
        failed_payments = random.randint(0, 10)
        customer_value = round(
            random.uniform(25000, 150000),
            2,
        )

    else:
        customer_age_days = random.randint(180, 2000)
        successful_payments = random.randint(30, 150)
        failed_payments = random.randint(0, 12)
        customer_value = round(
            random.uniform(100000, 500000),
            2,
        )

    total_payments = (
        successful_payments + failed_payments
    )

    if total_payments > 0:
        historical_success_rate = round(
            successful_payments / total_payments,
            4,
        )
    else:
        historical_success_rate = 0.0

    return {
        "customer_id": f"CUST_{customer_number:06d}",
        "customer_segment": segment,
        "customer_age_days": customer_age_days,
        "successful_payments": successful_payments,
        "failed_payments": failed_payments,
        "historical_success_rate": historical_success_rate,
        "customer_value": customer_value,
    }


# ============================================================
# FAILURE SELECTION
# ============================================================

def select_failure_reason(payment_method):
    if payment_method == "CARD":
        reasons = [
            "BANK_DECLINE",
            "INSUFFICIENT_FUNDS",
            "AUTHENTICATION_FAILED",
            "LIMIT_EXCEEDED",
            "EXPIRED_CARD",
            "NETWORK_ERROR",
        ]

    elif payment_method == "UPI":
        reasons = [
            "BANK_DECLINE",
            "NETWORK_ERROR",
            "LIMIT_EXCEEDED",
            "AUTHENTICATION_FAILED",
            "GATEWAY_TIMEOUT",
        ]

    elif payment_method == "NETBANKING":
        reasons = [
            "BANK_DECLINE",
            "NETWORK_ERROR",
            "GATEWAY_TIMEOUT",
            "AUTHENTICATION_FAILED",
        ]

    elif payment_method == "WALLET":
        reasons = [
            "INSUFFICIENT_FUNDS",
            "LIMIT_EXCEEDED",
            "NETWORK_ERROR",
            "BANK_DECLINE",
        ]

    else:
        reasons = [
            "MANDATE_FAILURE",
            "BANK_DECLINE",
            "INSUFFICIENT_FUNDS",
            "NETWORK_ERROR",
        ]

    return random.choice(reasons)


# ============================================================
# RECOVERY LOGIC
# ============================================================

def calculate_recovery_probability(
    customer,
    amount,
    payment_method,
    failure_reason,
    retry_count,
    subscription_status,
    hour,
):
    score = 0.0

    # Customer history
    score += (
        customer["historical_success_rate"] * 35
    )

    # Customer relationship
    if customer["customer_segment"] == "HIGH_VALUE":
        score += 18
    elif customer["customer_segment"] == "LOYAL":
        score += 12
    elif customer["customer_segment"] == "STANDARD":
        score += 6

    # Failure type
    recoverability = {
        "NETWORK_ERROR": 24,
        "GATEWAY_TIMEOUT": 22,
        "INSUFFICIENT_FUNDS": 17,
        "BANK_DECLINE": 10,
        "AUTHENTICATION_FAILED": 6,
        "LIMIT_EXCEEDED": 5,
        "EXPIRED_CARD": 3,
        "MANDATE_FAILURE": 8,
    }

    score += recoverability.get(
        failure_reason,
        5,
    )

    # Payment method behavior
    if payment_method == "UPI":
        score += 5
    elif payment_method == "CARD":
        score += 3
    elif payment_method == "EMANDATE":
        score += 2

    # Subscription state
    if subscription_status == "ACTIVE":
        score += 8
    elif subscription_status == "PAST_DUE":
        score += 3
    elif subscription_status == "CANCELLED":
        score -= 15

    # Retry fatigue
    score -= retry_count * 9

    # Large transaction amounts are slightly harder
    if amount > 100000:
        score -= 8
    elif amount > 50000:
        score -= 4

    # Mild time-of-day effect
    if 9 <= hour <= 21:
        score += 3
    else:
        score -= 2

    # Controlled noise
    score += random.uniform(
        -7,
        7,
    )

    return max(
        0.02,
        min(score / 100, 0.98),
    )


# ============================================================
# ACTION SELECTION
# ============================================================

def choose_recovery_action(
    failure_reason,
    recovery_probability,
    retry_count,
):
    if recovery_probability < 0.25:
        return "ESCALATE"

    if failure_reason in [
        "NETWORK_ERROR",
        "GATEWAY_TIMEOUT",
    ]:
        if retry_count < 2:
            return "SMART_RETRY"
        return "CUSTOMER_NOTIFICATION"

    if failure_reason == "INSUFFICIENT_FUNDS":
        return "CUSTOMER_NOTIFICATION"

    if failure_reason == "AUTHENTICATION_FAILED":
        return "PAYMENT_LINK"

    if failure_reason == "EXPIRED_CARD":
        return "PAYMENT_LINK"

    if failure_reason == "LIMIT_EXCEEDED":
        return "PAYMENT_LINK"

    if failure_reason == "MANDATE_FAILURE":
        return "MANDATE_RETRY"

    if failure_reason == "BANK_DECLINE":
        if retry_count < 1:
            return "SMART_RETRY"
        return "CUSTOMER_NOTIFICATION"

    return "CUSTOMER_NOTIFICATION"


# ============================================================
# DATASET GENERATION
# ============================================================

def generate_dataset():

    rows = []

    customer_cache = {}

    start_date = datetime.utcnow() - timedelta(
        days=365
    )

    for transaction_number in range(
        1,
        NUM_TRANSACTIONS + 1,
    ):

        # ----------------------------------------------------
        # CUSTOMER
        # ----------------------------------------------------

        customer_number = random.randint(
            1,
            2500,
        )

        if customer_number not in customer_cache:
            customer_cache[
                customer_number
            ] = generate_customer(
                customer_number
            )

        customer = customer_cache[
            customer_number
        ]

        # ----------------------------------------------------
        # TRANSACTION
        # ----------------------------------------------------

        transaction_id = (
            f"TXN_{transaction_number:08d}"
        )

        amount = round(
            np.random.lognormal(
                mean=8.2,
                sigma=1.05,
            ),
            2,
        )

        amount = max(
            100,
            min(amount, 500000),
        )

        payment_method = random.choices(
            PAYMENT_METHODS,
            weights=[42, 32, 12, 7, 7],
            k=1,
        )[0]

        merchant_category = random.choice(
            MERCHANT_CATEGORIES
        )

        subscription_status = random.choices(
            SUBSCRIPTION_STATUSES,
            weights=[55, 15, 20, 10],
            k=1,
        )[0]

        transaction_timestamp = (
            start_date
            + timedelta(
                minutes=random.randint(
                    0,
                    525600,
                )
            )
        )

        hour = transaction_timestamp.hour
        day_of_week = transaction_timestamp.weekday()

        # ----------------------------------------------------
        # SUCCESS / FAILURE
        # ----------------------------------------------------

        # Most transactions succeed.
        success_probability = (
            0.78
            + (
                customer[
                    "historical_success_rate"
                ]
                * 0.15
            )
        )

        if subscription_status == "CANCELLED":
            success_probability -= 0.15

        success_probability = max(
            0.35,
            min(success_probability, 0.96),
        )

        status = (
            "SUCCESS"
            if random.random()
            < success_probability
            else "FAILED"
        )

        if status == "SUCCESS":

            failure_reason = None
            retry_count = 0
            recovery_probability = 0.0
            recovery_possible = 0
            recovery_action = "NONE"
            actual_recovery = 0
            response_code = "SUCCESS"

        else:

            failure_reason = select_failure_reason(
                payment_method
            )

            retry_count = random.choices(
                [0, 1, 2, 3, 4],
                weights=[
                    50,
                    25,
                    15,
                    7,
                    3,
                ],
                k=1,
            )[0]

            recovery_probability = (
                calculate_recovery_probability(
                    customer=customer,
                    amount=amount,
                    payment_method=payment_method,
                    failure_reason=failure_reason,
                    retry_count=retry_count,
                    subscription_status=subscription_status,
                    hour=hour,
                )
            )

            recovery_possible = int(
                recovery_probability >= 0.50
            )

            recovery_action = choose_recovery_action(
                failure_reason,
                recovery_probability,
                retry_count,
            )

            # Simulated real-world outcome.
            recovered = (
                random.random()
                < recovery_probability
            )

            if recovered:
                actual_recovery = round(
                    amount
                    * random.uniform(
                        0.90,
                        1.00,
                    ),
                    2,
                )
            else:
                actual_recovery = 0

            response_code = RESPONSE_CODES.get(
                failure_reason,
                "UNKNOWN",
            )

        # ----------------------------------------------------
        # BUSINESS FEATURES
        # ----------------------------------------------------

        revenue_at_risk = round(
            amount * recovery_probability,
            2,
        )

        customer_value = customer[
            "customer_value"
        ]

        high_value_customer = int(
            customer_value >= 100000
        )

        previous_recovery_success = int(
            recovery_probability >= 0.65
        )

        # ----------------------------------------------------
        # FINAL ROW
        # ----------------------------------------------------

        rows.append(
            {
                "transaction_id": transaction_id,
                "customer_id": customer[
                    "customer_id"
                ],
                "customer_segment": customer[
                    "customer_segment"
                ],
                "customer_age_days": customer[
                    "customer_age_days"
                ],
                "successful_payments": customer[
                    "successful_payments"
                ],
                "failed_payments": customer[
                    "failed_payments"
                ],
                "historical_success_rate": customer[
                    "historical_success_rate"
                ],
                "customer_value": customer_value,
                "amount": amount,
                "payment_method": payment_method,
                "merchant_category": merchant_category,
                "subscription_status": subscription_status,
                "status": status,
                "failure_reason": failure_reason,
                "retry_count": retry_count,
                "transaction_timestamp": transaction_timestamp.isoformat(),
                "hour": hour,
                "day_of_week": day_of_week,
                "recovery_probability": round(
                    recovery_probability,
                    4,
                ),
                "recovery_possible": recovery_possible,
                "recovery_action": recovery_action,
                "revenue_at_risk": revenue_at_risk,
                "actual_recovery": actual_recovery,
                "high_value_customer": high_value_customer,
                "previous_recovery_success": previous_recovery_success,
                "response_code": response_code,
            }
        )

    df = pd.DataFrame(rows)

    # --------------------------------------------------------
    # SHUFFLE
    # --------------------------------------------------------

    df = df.sample(
        frac=1,
        random_state=SEED,
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("=" * 60)
    print("AI REVENUE RECOVERY DATASET")
    print("=" * 60)

    print(f"Rows generated: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Saved to: {OUTPUT_FILE}")

    print("\nTransaction status:")
    print(
        df["status"].value_counts()
    )

    print("\nRecovery target:")
    print(
        df["recovery_possible"].value_counts()
    )

    print("\nFailure reasons:")
    print(
        df["failure_reason"]
        .value_counts(dropna=True)
    )

    print("\nRecovery actions:")
    print(
        df["recovery_action"]
        .value_counts()
    )

    failed_df = df[
        df["status"] == "FAILED"
    ]

    print("\nFailed transaction statistics:")

    if not failed_df.empty:
        print(
            f"Failed transactions: "
            f"{len(failed_df):,}"
        )

        print(
            f"Revenue at risk: "
            f"₹{failed_df['revenue_at_risk'].sum():,.2f}"
        )

        print(
            f"Potential recovered revenue: "
            f"₹{failed_df['actual_recovery'].sum():,.2f}"
        )

        print(
            f"Recoverable failures: "
            f"{failed_df['recovery_possible'].mean() * 100:.2f}%"
        )

    print("=" * 60)


if __name__ == "__main__":
    generate_dataset()