from pathlib import Path

from sqlalchemy.orm import joinedload

from database.db import db
from models.transaction import Transaction
from models.customer import Customer
from models.recovery_outcome import RecoveryOutcome
from ml.predict_recovery import predict_recovery_batch


BASE_DIR = Path(__file__).resolve().parent.parent


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _format_currency(value):
    value = _safe_float(value)

    if value >= 10_000_000:
        return f"₹{value / 10_000_000:.2f}Cr"

    if value >= 100_000:
        return f"₹{value / 100_000:.2f}L"

    if value >= 1_000:
        return f"₹{value / 1_000:.1f}K"

    return f"₹{value:,.0f}"


def _feature_row(transaction):
    customer = transaction.customer

    successful_payments = int(
        customer.successful_payments or 0
    )

    failed_payments = int(
        customer.failed_payments or 0
    )

    historical_success_rate = _safe_float(
        customer.historical_success_rate
    )

    customer_age_days = 0

    if (
        customer.customer_since
        and transaction.transaction_timestamp
    ):
        customer_age_days = max(
            0,
            (
                transaction.transaction_timestamp
                - customer.customer_since
            ).days,
        )

    hour = (
        transaction.transaction_timestamp.hour
        if transaction.transaction_timestamp
        else 12
    )

    day_of_week = (
        transaction.transaction_timestamp.weekday()
        if transaction.transaction_timestamp
        else 0
    )

    previous_recovery_success = 0

    for outcome in transaction.recovery_outcomes:
        if _safe_float(
            outcome.amount_recovered
        ) > 0:
            previous_recovery_success = 1
            break

    high_value_customer = (
        1
        if _safe_float(
            customer.customer_value
        ) >= 100000
        else 0
    )

    return {
        "customer_segment": customer.customer_segment,
        "customer_age_days": customer_age_days,
        "successful_payments": successful_payments,
        "failed_payments": failed_payments,
        "historical_success_rate": historical_success_rate,
        "customer_value": _safe_float(
            customer.customer_value
        ),
        "amount": _safe_float(
            transaction.amount
        ),
        "payment_method": transaction.payment_method,
        "merchant_category": transaction.merchant_category,
        "subscription_status": (
            transaction.subscription_status
            or "UNKNOWN"
        ),
        "retry_count": int(
            transaction.retry_count or 0
        ),
        "hour": hour,
        "day_of_week": day_of_week,
        "failure_reason": (
            transaction.failure_reason
            or "UNKNOWN"
        ),
        "high_value_customer": high_value_customer,
        "previous_recovery_success": (
            previous_recovery_success
        ),
        "response_code": None,
    }


def _load_failed_transactions():
    return (
        Transaction.query
        .options(
            joinedload(
                Transaction.customer
            ),
            joinedload(
                Transaction.recovery_outcomes
            ),
        )
        .filter(
            Transaction.status.ilike("FAILED")
        )
        .order_by(
            Transaction.transaction_timestamp.desc()
        )
        .all()
    )


def _get_recovery_amounts(transactions):
    transaction_ids = [
        transaction.id
        for transaction in transactions
    ]

    if not transaction_ids:
        return {}

    outcomes = (
        RecoveryOutcome.query
        .filter(
            RecoveryOutcome.transaction_id.in_(
                transaction_ids
            )
        )
        .all()
    )

    recovery_amounts = {}

    for outcome in outcomes:
        transaction_id = outcome.transaction_id

        amount = _safe_float(
            outcome.amount_recovered
        )

        recovery_amounts[transaction_id] = (
            recovery_amounts.get(
                transaction_id,
                0.0,
            )
            + amount
        )

    return recovery_amounts


def _action_for_transaction(
    transaction,
    probability,
):
    reason = str(
        transaction.failure_reason or ""
    ).upper()

    retry_count = int(
        transaction.retry_count or 0
    )

    if retry_count >= 3:
        return "CUSTOMER REMINDER"

    if (
        "AUTH" in reason
        or "VERIFICATION" in reason
    ):
        return "PAYMENT LINK"

    if (
        "INSUFFICIENT" in reason
        or "BALANCE" in reason
    ):
        return "PAYMENT LINK"

    if probability >= 65:
        return "SMART RETRY"

    if probability >= 40:
        return "CUSTOMER REMINDER"

    return "ESCALATION"


def _simulate(
    transactions,
    predictions,
    min_probability,
    max_retries,
    recovery_amounts,
):
    eligible = []
    attempted = []
    recovered = []

    for transaction, prediction in zip(
        transactions,
        predictions,
    ):
        probability = (
            _safe_float(
                prediction.get(
                    "recovery_probability",
                    0,
                )
            )
            * 100
        )

        if probability < min_probability:
            continue

        retry_count = int(
            transaction.retry_count or 0
        )

        if retry_count >= max_retries:
            continue

        amount = _safe_float(
            transaction.amount
        )

        expected_recovery = (
            amount * probability / 100
        )

        recommended_action = (
            _action_for_transaction(
                transaction,
                probability,
            )
        )

        recovered_amount = (
            recovery_amounts.get(
                transaction.id,
                0.0,
            )
        )

        item = {
            "transaction": transaction,
            "probability": probability,
            "amount": amount,
            "expected_recovery": (
                expected_recovery
            ),
            "recommended_action": (
                recommended_action
            ),
            "recovered_amount": (
                recovered_amount
            ),
            "retry_count": retry_count,
        }

        eligible.append(item)

        guardrail_passed = (
            probability >= min_probability
            and retry_count < max_retries
        )

        if guardrail_passed:
            attempted.append(item)

            if recovered_amount > 0:
                recovered.append(item)

    return (
        eligible,
        attempted,
        recovered,
    )


def _build_action_distribution(
    attempted,
):
    if not attempted:
        return []

    groups = {}

    for item in attempted:
        action = item[
            "recommended_action"
        ]

        if action not in groups:
            groups[action] = {
                "count": 0,
                "revenue": 0.0,
                "recovered": 0.0,
            }

        groups[action]["count"] += 1

        groups[action]["revenue"] += (
            item["amount"]
        )

        groups[action]["recovered"] += (
            item["recovered_amount"]
        )

    total = len(attempted)

    results = []

    for action, values in groups.items():
        revenue = values["revenue"]
        recovered = values["recovered"]

        results.append(
            {
                "action": action,
                "count": values["count"],
                "share": round(
                    values["count"]
                    / total
                    * 100,
                    1,
                ),
                "revenue": revenue,
                "revenue_display": (
                    _format_currency(
                        revenue
                    )
                ),
                "recovered": recovered,
                "recovered_display": (
                    _format_currency(
                        recovered
                    )
                ),
            }
        )

    results.sort(
        key=lambda item: item["count"],
        reverse=True,
    )

    return results


def _build_funnel(
    failed,
    eligible,
    attempted,
    recovered,
):
    failed_revenue = sum(
        _safe_float(
            transaction.amount
        )
        for transaction in failed
    )

    eligible_revenue = sum(
        item["amount"]
        for item in eligible
    )

    attempted_revenue = sum(
        item["amount"]
        for item in attempted
    )

    recovered_revenue = sum(
        item["recovered_amount"]
        for item in recovered
    )

    return [
        {
            "stage": "Failed Payments",
            "value": len(failed),
            "revenue": round(
                failed_revenue,
                2,
            ),
        },
        {
            "stage": "Recovery Opportunities",
            "value": len(eligible),
            "revenue": round(
                eligible_revenue,
                2,
            ),
        },
        {
            "stage": "Guardrail Approved",
            "value": len(attempted),
            "revenue": round(
                attempted_revenue,
                2,
            ),
        },
        {
            "stage": "Recovered",
            "value": len(recovered),
            "revenue": round(
                recovered_revenue,
                2,
            ),
        },
    ]


def run_simulation(
    min_probability=40,
    max_retries=3,
    batch_size=1000,
):
    min_probability = max(
        0.0,
        min(
            _safe_float(
                min_probability,
                40.0,
            ),
            100.0,
        ),
    )

    max_retries = max(
        0,
        int(max_retries),
    )

    batch_size = max(
        100,
        min(
            int(batch_size),
            10000,
        ),
    )

    failed = _load_failed_transactions()

    if len(failed) > batch_size:
        failed = failed[:batch_size]

    if not failed:
        return {
            "parameters": {
                "batch_size": batch_size,
                "min_probability": (
                    min_probability
                ),
                "max_retries": max_retries,
            },
            "summary": {
                "failed_payments": 0,
                "eligible_opportunities": 0,
                "revenue_at_risk": 0,
                "revenue_at_risk_display": "₹0",
                "expected_recovery": 0,
                "expected_recovery_display": "₹0",
                "recovered_revenue": 0,
                "recovered_revenue_display": "₹0",
                "recovery_rate": 0,
                "attempted": 0,
                "recovered_transactions": 0,
                "guardrail_blocked": 0,
            },
            "funnel": _build_funnel(
                [],
                [],
                [],
                [],
            ),
            "actions": [],
            "insight": {
                "title": (
                    "No failed payments "
                    "available"
                ),
                "description": (
                    "There are no failed "
                    "transactions available "
                    "for simulation."
                ),
            },
        }

    feature_rows = [
        _feature_row(transaction)
        for transaction in failed
    ]

    predictions = predict_recovery_batch(
        feature_rows
    )

    recovery_amounts = (
        _get_recovery_amounts(
            failed
        )
    )

    (
        eligible,
        attempted,
        recovered,
    ) = _simulate(
        failed,
        predictions,
        min_probability,
        max_retries,
        recovery_amounts,
    )

    # Full transaction amount currently exposed
    # to recovery among eligible opportunities.
    revenue_at_risk = sum(
        item["amount"]
        for item in eligible
    )

    # Probability-weighted amount expected
    # to be recovered from those opportunities.
    expected_recovery = sum(
        item["expected_recovery"]
        for item in eligible
    )

    recovered_revenue = sum(
        item["recovered_amount"]
        for item in recovered
    )

    attempted_revenue = sum(
        item["amount"]
        for item in attempted
    )

    recovery_rate = (
        recovered_revenue
        / attempted_revenue
        * 100
        if attempted_revenue > 0
        else 0
    )

    guardrail_blocked = max(
        0,
        len(eligible)
        - len(attempted),
    )

    actions = _build_action_distribution(
        attempted
    )

    funnel = _build_funnel(
        failed,
        eligible,
        attempted,
        recovered,
    )

    return {
        "parameters": {
            "batch_size": batch_size,
            "min_probability": (
                min_probability
            ),
            "max_retries": max_retries,
        },
        "summary": {
            "failed_payments": len(failed),
            "eligible_opportunities": len(
                eligible
            ),
            "revenue_at_risk": round(
                revenue_at_risk,
                2,
            ),
            "revenue_at_risk_display": (
                _format_currency(
                    revenue_at_risk
                )
            ),
            "expected_recovery": round(
                expected_recovery,
                2,
            ),
            "expected_recovery_display": (
                _format_currency(
                    expected_recovery
                )
            ),
            "recovered_revenue": round(
                recovered_revenue,
                2,
            ),
            "recovered_revenue_display": (
                _format_currency(
                    recovered_revenue
                )
            ),
            "recovery_rate": round(
                recovery_rate,
                1,
            ),
            "attempted": len(attempted),
            "recovered_transactions": len(
                recovered
            ),
            "guardrail_blocked": (
                guardrail_blocked
            ),
        },
        "funnel": funnel,
        "actions": actions,
        "insight": {
            "title": (
                f"Simulation identifies "
                f"{len(eligible)} "
                f"recovery opportunities"
            ),
            "description": (
                f"Under the selected policy, "
                f"{len(attempted)} opportunities "
                f"passed guardrail validation and "
                f"{_format_currency(recovered_revenue)} "
                f"was recovered in the simulated "
                f"batch."
            ),
        },
    }