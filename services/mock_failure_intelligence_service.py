from math import ceil

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database.db import db
from models import Transaction, Customer, RecoveryOutcome
from ml.predict_recovery import predict_recovery_batch


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_string(value, default=""):
    if value is None:
        return default
    return str(value)


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

    historical_success_rate = _safe_float(
        customer.historical_success_rate
    )

    if historical_success_rate > 1:
        historical_success_rate /= 100

    customer_value = _safe_float(
        customer.customer_value
    )

    successful_payments = _safe_int(
        customer.successful_payments
    )

    failed_payments = _safe_int(
        customer.failed_payments
    )

    return {
        "customer_segment": _safe_string(
            customer.customer_segment,
            "STANDARD",
        ),
        "customer_age_days": (
            (
                transaction.transaction_timestamp
                - customer.customer_since
            ).days
            if (
                transaction.transaction_timestamp
                and customer.customer_since
            )
            else 0
        ),
        "successful_payments": successful_payments,
        "failed_payments": failed_payments,
        "historical_success_rate": historical_success_rate,
        "customer_value": customer_value,
        "amount": _safe_float(
            transaction.amount
        ),
        "payment_method": _safe_string(
            transaction.payment_method
        ),
        "merchant_category": _safe_string(
            transaction.merchant_category
        ),
        "subscription_status": _safe_string(
            transaction.subscription_status
        ),
        "status": _safe_string(
            transaction.status
        ),
        "failure_reason": _safe_string(
            transaction.failure_reason,
            "UNKNOWN",
        ),
        "retry_count": _safe_int(
            transaction.retry_count
        ),
        "hour": (
            transaction.transaction_timestamp.hour
            if transaction.transaction_timestamp
            else 0
        ),
        "day_of_week": (
            transaction.transaction_timestamp.weekday()
            if transaction.transaction_timestamp
            else 0
        ),
        "previous_recovery_success": int(
            successful_payments > 0
        ),
        "high_value_customer": int(
            customer_value >= 100000
        ),
    }


def _load_failed_transactions():
    return (
        Transaction.query
        .options(
            joinedload(Transaction.customer)
        )
        .filter(
            Transaction.status.ilike("FAILED")
        )
        .order_by(
            Transaction.transaction_timestamp.asc()
        )
        .all()
    )


def _get_recovery_amounts():
    rows = (
        db.session.query(
            RecoveryOutcome.transaction_id,
            func.sum(
                RecoveryOutcome.amount_recovered
            )
        )
        .group_by(
            RecoveryOutcome.transaction_id
        )
        .all()
    )

    return {
        transaction_id: _safe_float(amount)
        for transaction_id, amount in rows
    }


def _predict_transactions(transactions):
    if not transactions:
        return []

    feature_rows = [
        _feature_row(transaction)
        for transaction in transactions
    ]

    predictions = predict_recovery_batch(
        feature_rows
    )

    return [
        _safe_float(
            prediction.get(
                "recovery_percentage",
                0,
            )
        )
        for prediction in predictions
    ]


def _build_failure_reasons(
    transactions,
    probabilities,
    recovery_amounts,
):
    grouped = {}

    for transaction, probability in zip(
        transactions,
        probabilities,
    ):
        reason = _safe_string(
            transaction.failure_reason,
            "UNKNOWN",
        ).upper()

        bucket = grouped.setdefault(
            reason,
            {
                "transactions": 0,
                "revenue_lost": 0.0,
                "revenue_at_risk": 0.0,
                "probabilities": [],
                "recovered_revenue": 0.0,
            },
        )

        amount = _safe_float(
            transaction.amount
        )

        bucket["transactions"] += 1
        bucket["revenue_lost"] += amount
        bucket["revenue_at_risk"] += 0
        bucket["revenue_at_risk"] += (
            amount
            * probability
            / 100
        )
        bucket["probabilities"].append(
            probability
        )

        bucket["recovered_revenue"] += (
            recovery_amounts.get(
                transaction.id,
                0,
            )
        )

    total_transactions = len(
        transactions
    )

    results = []

    for reason, bucket in grouped.items():
        transaction_count = bucket[
            "transactions"
        ]

        recoverability = (
            sum(bucket["probabilities"])
            / len(bucket["probabilities"])
            if bucket["probabilities"]
            else 0
        )

        revenue_lost = bucket[
            "revenue_lost"
        ]

        revenue_at_risk = bucket[
            "revenue_at_risk"
        ]

        recovered_revenue = bucket[
            "recovered_revenue"
        ]

        results.append(
            {
                "failure_reason": reason,
                "transactions": transaction_count,
                "share": round(
                    transaction_count
                    / total_transactions
                    * 100,
                    1,
                ),
                "revenue_lost": round(
                    revenue_lost,
                    2,
                ),
                "revenue_lost_display":
                    _format_currency(
                        revenue_lost
                    ),
                "revenue_at_risk": round(
                    revenue_at_risk,
                    2,
                ),
                "revenue_at_risk_display":
                    _format_currency(
                        revenue_at_risk
                    ),
                "recoverability": round(
                    recoverability,
                    1,
                ),
                "recovered_revenue": round(
                    recovered_revenue,
                    2,
                ),
                "recovered_revenue_display":
                    _format_currency(
                        recovered_revenue
                    ),
            }
        )

    results.sort(
        key=lambda item: item[
            "revenue_lost"
        ],
        reverse=True,
    )

    return results


def _build_payment_methods(
    transactions,
    probabilities,
):
    grouped = {}

    for transaction, probability in zip(
        transactions,
        probabilities,
    ):
        method = _safe_string(
            transaction.payment_method,
            "UNKNOWN",
        ).upper()

        bucket = grouped.setdefault(
            method,
            {
                "transactions": 0,
                "revenue_lost": 0.0,
                "probabilities": [],
            },
        )

        bucket["transactions"] += 1
        bucket["revenue_lost"] += (
            _safe_float(
                transaction.amount
            )
        )
        bucket["probabilities"].append(
            probability
        )

    results = []

    for method, bucket in grouped.items():
        probabilities_list = bucket[
            "probabilities"
        ]

        recoverability = (
            sum(probabilities_list)
            / len(probabilities_list)
            if probabilities_list
            else 0
        )

        revenue_lost = bucket[
            "revenue_lost"
        ]

        results.append(
            {
                "payment_method": method,
                "transactions": bucket[
                    "transactions"
                ],
                "revenue_lost": round(
                    revenue_lost,
                    2,
                ),
                "revenue_lost_display":
                    _format_currency(
                        revenue_lost
                    ),
                "recoverability": round(
                    recoverability,
                    1,
                ),
            }
        )

    results.sort(
        key=lambda item: item[
            "revenue_lost"
        ],
        reverse=True,
    )

    return results


def _build_trend(
    transactions,
    recovery_amounts,
):
    grouped = {}

    for transaction in transactions:
        timestamp = (
            transaction.transaction_timestamp
        )

        if not timestamp:
            continue

        date = timestamp.date()

        bucket = grouped.setdefault(
            date,
            {
                "transactions": 0,
                "revenue_lost": 0.0,
                "revenue_at_risk": 0.0,
                "recovered_revenue": 0.0,
            },
        )

        amount = _safe_float(
            transaction.amount
        )

        bucket["transactions"] += 1
        bucket["revenue_lost"] += amount

        bucket["recovered_revenue"] += (
            recovery_amounts.get(
                transaction.id,
                0,
            )
        )

    results = []

    for date, bucket in sorted(
        grouped.items()
    ):
        results.append(
            {
                "date": str(date),
                "transactions": bucket[
                    "transactions"
                ],
                "revenue_lost": round(
                    bucket["revenue_lost"],
                    2,
                ),
                "revenue_lost_display":
                    _format_currency(
                        bucket[
                            "revenue_lost"
                        ]
                    ),
                "revenue_at_risk": round(
                    bucket[
                        "revenue_at_risk"
                    ],
                    2,
                ),
                "recovered_revenue": round(
                    bucket[
                        "recovered_revenue"
                    ],
                    2,
                ),
            }
        )

    return results


def _build_high_risk_patterns(
    transactions,
    probabilities,
    recovery_amounts,
):
    grouped = {}

    for transaction, probability in zip(
        transactions,
        probabilities,
    ):
        reason = _safe_string(
            transaction.failure_reason,
            "UNKNOWN",
        ).upper()

        method = _safe_string(
            transaction.payment_method,
            "UNKNOWN",
        ).upper()

        key = (
            reason,
            method,
        )

        bucket = grouped.setdefault(
            key,
            {
                "transactions": 0,
                "revenue_at_risk": 0.0,
                "probabilities": [],
                "recovered_revenue": 0.0,
            },
        )

        amount = _safe_float(
            transaction.amount
        )

        bucket["transactions"] += 1
        bucket["revenue_at_risk"] += (
            amount
            * probability
            / 100
        )

        bucket["probabilities"].append(
            probability
        )

        bucket["recovered_revenue"] += (
            recovery_amounts.get(
                transaction.id,
                0,
            )
        )

    results = []

    for (
        reason,
        method,
    ), bucket in grouped.items():

        probabilities_list = bucket[
            "probabilities"
        ]

        recoverability = (
            sum(probabilities_list)
            / len(probabilities_list)
            if probabilities_list
            else 0
        )

        revenue_at_risk = bucket[
            "revenue_at_risk"
        ]

        opportunity_score = (
            revenue_at_risk
            * max(
                recoverability,
                1,
            )
            / 100
        )

        results.append(
            {
                "failure_reason": reason,
                "payment_method": method,
                "transactions": bucket[
                    "transactions"
                ],
                "revenue_at_risk": round(
                    revenue_at_risk,
                    2,
                ),
                "revenue_at_risk_display":
                    _format_currency(
                        revenue_at_risk
                    ),
                "recoverability": round(
                    recoverability,
                    1,
                ),
                "recovered_revenue": round(
                    bucket[
                        "recovered_revenue"
                    ],
                    2,
                ),
                "recovered_revenue_display":
                    _format_currency(
                        bucket[
                            "recovered_revenue"
                        ]
                    ),
                "opportunity_score": round(
                    opportunity_score,
                    2,
                ),
            }
        )

    results.sort(
        key=lambda item: item[
            "opportunity_score"
        ],
        reverse=True,
    )

    return results[:6]


def _build_insight(
    failed,
    failure_reasons,
    payment_methods,
):
    if not failed:
        return {
            "title":
                "No failure intelligence available",
            "description":
                "No failed payment events are currently "
                "available for analysis.",
            "severity": "LOW",
        }

    top_failure = (
        failure_reasons[0]
        if failure_reasons
        else None
    )

    if top_failure:
        reason = top_failure[
            "failure_reason"
        ]

        recoverability = top_failure[
            "recoverability"
        ]

        revenue = top_failure[
            "revenue_lost_display"
        ]

        if recoverability >= 60:
            severity = "HIGH"
            description = (
                f"{reason.replace('_', ' ').title()} "
                f"is the largest failure driver by revenue, "
                f"with {revenue} exposed and "
                f"{recoverability:.1f}% average recoverability. "
                "This pattern represents a strong recovery "
                "opportunity for targeted intervention."
            )

        elif recoverability >= 35:
            severity = "MEDIUM"
            description = (
                f"{reason.replace('_', ' ').title()} contributes "
                f"{revenue} of failed-payment exposure with "
                f"{recoverability:.1f}% average recoverability. "
                "Selective recovery actions should be prioritized "
                "for eligible transactions."
            )

        else:
            severity = "LOW"
            description = (
                f"{reason.replace('_', ' ').title()} contributes "
                f"{revenue} of failed-payment exposure, but its "
                f"{recoverability:.1f}% recoverability suggests "
                "limited automatic recovery potential."
            )

        return {
            "title": (
                f"{reason.replace('_', ' ').title()} "
                "is the leading failure driver"
            ),
            "description": description,
            "severity": severity,
        }

    return {
        "title": "Failure patterns detected",
        "description": (
            "RecoverAI has identified failed-payment "
            "patterns requiring further recovery analysis."
        ),
        "severity": "MEDIUM",
    }


def get_failure_intelligence():
    failed = _load_failed_transactions()

    if not failed:
        return {
            "summary": {
                "failed_transactions": 0,
                "revenue_lost": 0,
                "revenue_at_risk": 0,
                "recovered_revenue": 0,
                "failure_rate": 0,
                "recoverability": 0,
            },
            "failure_reasons": [],
            "payment_methods": [],
            "trend": [],
            "high_risk_patterns": [],
            "insight": {
                "title":
                    "No failure intelligence available",
                "description":
                    "No failed payment events were found.",
                "severity": "LOW",
            },
        }

    probabilities = _predict_transactions(
        failed
    )

    recovery_amounts = (
        _get_recovery_amounts()
    )

    total_transactions = (
        Transaction.query.count()
    )

    failed_transactions = len(
        failed
    )

    revenue_lost = sum(
        _safe_float(
            transaction.amount
        )
        for transaction in failed
    )

    revenue_at_risk = sum(
        _safe_float(
            transaction.amount
        )
        * probability
        / 100
        for transaction, probability
        in zip(
            failed,
            probabilities,
        )
    )

    recovered_revenue = sum(
        recovery_amounts.get(
            transaction.id,
            0,
        )
        for transaction in failed
    )

    failure_rate = (
        round(
            failed_transactions
            / total_transactions
            * 100,
            1,
        )
        if total_transactions
        else 0
    )

    recoverability = (
        round(
            sum(probabilities)
            / len(probabilities),
            1,
        )
        if probabilities
        else 0
    )

    failure_reasons = (
        _build_failure_reasons(
            failed,
            probabilities,
            recovery_amounts,
        )
    )

    payment_methods = (
        _build_payment_methods(
            failed,
            probabilities,
        )
    )

    trend = _build_trend(
        failed,
        recovery_amounts,
    )

    high_risk_patterns = (
        _build_high_risk_patterns(
            failed,
            probabilities,
            recovery_amounts,
        )
    )

    insight = _build_insight(
        failed,
        failure_reasons,
        payment_methods,
    )

    return {
        "summary": {
            "failed_transactions":
                failed_transactions,
            "revenue_lost":
                round(
                    revenue_lost,
                    2,
                ),
            "revenue_lost_display":
                _format_currency(
                    revenue_lost
                ),
            "revenue_at_risk":
                round(
                    revenue_at_risk,
                    2,
                ),
            "revenue_at_risk_display":
                _format_currency(
                    revenue_at_risk
                ),
            "recovered_revenue":
                round(
                    recovered_revenue,
                    2,
                ),
            "recovered_revenue_display":
                _format_currency(
                    recovered_revenue
                ),
            "failure_rate":
                failure_rate,
            "recoverability":
                recoverability,
        },
        "failure_reasons":
            failure_reasons,
        "payment_methods":
            payment_methods,
        "trend":
            trend,
        "high_risk_patterns":
            high_risk_patterns,
        "insight":
            insight,
    }