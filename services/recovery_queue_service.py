from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from database.db import db
from models.transaction import Transaction

from ml.predict_recovery import (
    predict_recovery_batch,
    calculate_revenue_at_risk,
)


def _format_currency(amount):
    amount = float(amount or 0)

    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f}Cr"

    if amount >= 100_000:
        return f"₹{amount / 100_000:.2f}L"

    if amount >= 1_000:
        return f"₹{amount / 1_000:.1f}K"

    return f"₹{amount:,.0f}"


def _priority(probability, amount, retry_count):
    score = (
        probability * 0.60
        + min(float(amount) / 100000, 1) * 25
        + max(0, 3 - retry_count) * 5
    )

    if score >= 70:
        return "HIGH"

    if score >= 45:
        return "MEDIUM"

    return "LOW"


def _recommended_action(failure_reason, probability, retry_count):
    reason = str(failure_reason or "").lower()

    if probability < 35:
        return "STOP"

    if "network" in reason or "timeout" in reason:
        return "SMART RETRY"

    if "authentication" in reason:
        return "AUTHENTICATION RETRY"

    if "bank" in reason:
        return "PAYMENT RETRY"

    if "insufficient" in reason:
        return "CUSTOMER REMINDER"

    if retry_count >= 3:
        return "CUSTOMER REMINDER"

    return "SMART RETRY"


def _status(probability):
    if probability >= 70:
        return "READY"

    if probability >= 45:
        return "PENDING"

    return "STOPPED"


def _guardrail(probability, retry_count):
    if probability < 35:
        return "BLOCKED"

    if retry_count >= 3:
        return "REVIEW"

    return "PASSED"


def get_recovery_queue(
    search=None,
    min_probability=0,
    max_retries=3,
    page=1,
    per_page=10,
):
    query = (
        Transaction.query
        .options(joinedload(Transaction.customer))
        .filter(
            Transaction.status.ilike("FAILED"),
            Transaction.retry_count < max_retries,
        )
    )

    if search:
        search_term = f"%{search.strip()}%"

        query = query.filter(
            or_(
                Transaction.transaction_id.ilike(search_term),
                Transaction.failure_reason.ilike(search_term),
            )
        )

    transactions = (
        query
        .order_by(
            Transaction.transaction_timestamp.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # Build all ML feature rows first
    # --------------------------------------------------------

    candidates = []
    feature_rows = []

    for transaction in transactions:
        customer = transaction.customer

        if not customer:
            continue

        timestamp = transaction.transaction_timestamp

        customer_age_days = max(
            (
                timestamp - customer.customer_since
            ).days,
            0,
        )

        high_value_customer = (
            float(customer.customer_value) >= 100000
        )

        previous_recovery_success = False

        feature_rows.append({
            "amount": float(transaction.amount),
            "payment_method": transaction.payment_method,
            "merchant_category": transaction.merchant_category,
            "failure_reason": (
                transaction.failure_reason
                or "Unknown"
            ),
            "retry_count": transaction.retry_count,
            "customer_segment": customer.customer_segment,
            "customer_age_days": customer_age_days,
            "successful_payments": customer.successful_payments,
            "failed_payments": customer.failed_payments,
            "historical_success_rate": (
                customer.historical_success_rate
            ),
            "customer_value": float(
                customer.customer_value
            ),
            "subscription_status": (
                transaction.subscription_status
                or "Unknown"
            ),
            "hour": timestamp.hour,
            "day_of_week": timestamp.weekday(),
            "high_value_customer": high_value_customer,
            "previous_recovery_success": (
                previous_recovery_success
            ),
        })

        candidates.append({
            "transaction": transaction,
            "customer": customer,
            "timestamp": timestamp,
            "customer_age_days": customer_age_days,
            "high_value_customer": high_value_customer,
        })

    # --------------------------------------------------------
    # ONE BATCH ML PREDICTION
    # --------------------------------------------------------

    predictions = predict_recovery_batch(feature_rows)

    opportunities = []

    for candidate, prediction in zip(
        candidates,
        predictions,
    ):
        transaction = candidate["transaction"]
        customer = candidate["customer"]
        timestamp = candidate["timestamp"]

        probability = prediction["recovery_percentage"]

        if probability < float(min_probability):
            continue

        amount = float(transaction.amount)

        
# Full failed transaction amount currently at risk
        revenue_at_risk = amount

# ML probability-weighted amount expected to be recovered
        expected_recovery = calculate_revenue_at_risk(
            amount,
            prediction["recovery_probability"],
        )

        priority = _priority(
            probability,
            amount,
            transaction.retry_count,
        )

        action = _recommended_action(
            transaction.failure_reason,
            probability,
            transaction.retry_count,
        )

        status = _status(probability)

        guardrail = _guardrail(
            probability,
            transaction.retry_count,
        )

        opportunities.append({
            "transaction_id": transaction.transaction_id,
            "customer_id": customer.customer_id,
            "customer_label": customer.customer_id,
            "customer_segment": customer.customer_segment,

            "amount": round(amount, 2),
            "amount_label": _format_currency(amount),

            "failure_reason": (
                transaction.failure_reason
                or "Unknown"
            ),

            "payment_method": transaction.payment_method,

            "recovery_probability": round(
                probability,
                1,
            ),

            "revenue_at_risk": round(
                revenue_at_risk,
                2,
            ),

            "revenue_at_risk_label": _format_currency(
                revenue_at_risk
            ),

            "expected_recovery": round(
                expected_recovery,
                2,
            ),

            "expected_recovery_label": _format_currency(
                expected_recovery
            ),

            "priority": priority,
            "recommended_action": action,
            "guardrail": guardrail,
            "status": status,

            "retry_count": transaction.retry_count,

            "high_value_customer": (
                candidate["high_value_customer"]
            ),

            "subscription_status": (
                transaction.subscription_status
                or "UNKNOWN"
            ),

            "timestamp": timestamp.isoformat(),
        })

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    opportunities.sort(
        key=lambda item: (
            {
                "HIGH": 3,
                "MEDIUM": 2,
                "LOW": 1,
            }.get(
                item["priority"],
                0,
            ),
            item["expected_recovery"],
            item["amount"],
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_opportunities = len(opportunities)

    revenue_at_risk = sum(
        item["revenue_at_risk"]
        for item in opportunities
    )

    expected_recovery = sum(
        item["expected_recovery"]
        for item in opportunities
    )

    high_priority = sum(
        1
        for item in opportunities
        if item["priority"] == "HIGH"
    )

    recovery_potential = (
        (
            expected_recovery
            / revenue_at_risk
        ) * 100
        if revenue_at_risk > 0
        else 0
    )

    # --------------------------------------------------------
    # FAILURE DRIVERS
    # --------------------------------------------------------

    driver_counts = {}

    for item in opportunities:
        reason = item["failure_reason"]

        driver_counts[reason] = (
            driver_counts.get(reason, 0) + 1
        )

    total_driver_volume = max(
        sum(driver_counts.values()),
        1,
    )

    drivers = []

    for reason, volume in sorted(
        driver_counts.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]:

        drivers.append({
            "name": reason,
            "volume": volume,
            "share": round(
                volume
                / total_driver_volume
                * 100,
                1,
            ),
        })

    # --------------------------------------------------------
    # PAYMENT METHODS
    # --------------------------------------------------------

    payment_counts = {}

    for item in opportunities:
        method = item["payment_method"]

        payment_counts[method] = (
            payment_counts.get(method, 0) + 1
        )

    total_payment_volume = max(
        sum(payment_counts.values()),
        1,
    )

    payment_methods = []

    for method, volume in sorted(
        payment_counts.items(),
        key=lambda x: x[1],
        reverse=True,
    ):

        payment_methods.append({
            "name": method,
            "volume": volume,
            "share": round(
                volume
                / total_payment_volume
                * 100,
                1,
            ),
        })

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    per_page = max(
        1,
        min(int(per_page), 50),
    )

    page = max(
        int(page),
        1,
    )

    total_pages = max(
        1,
        (
            total_opportunities
            + per_page
            - 1
        ) // per_page,
    )

    page = min(
        page,
        total_pages,
    )

    start = (
        page - 1
    ) * per_page

    end = start + per_page

    paginated = opportunities[
        start:end
    ]

    strategy_priority = (
        "HIGH"
        if high_priority > 0
        else "MEDIUM"
        if total_opportunities > 0
        else "LOW"
    )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "summary": {
            "eligible_opportunities":
                total_opportunities,

            "eligible_opportunities_label":
                f"{total_opportunities:,}",

            "revenue_at_risk":
                round(
                    revenue_at_risk,
                    2,
                ),

            "revenue_at_risk_label":
                _format_currency(
                    revenue_at_risk
                ),

            "expected_recovery":
                round(
                    expected_recovery,
                    2,
                ),

            "expected_recovery_label":
                _format_currency(
                    expected_recovery
                ),

            "high_priority":
                high_priority,

            "high_priority_label":
                f"{high_priority:,}",

            "recovery_potential":
                round(
                    recovery_potential,
                    1,
                ),
        },

        "opportunities": paginated,

        "drivers": drivers,

        "payment_methods": payment_methods,

        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_opportunities,
            "total_pages": total_pages,
        },

        "ai_strategy": {
            "priority": strategy_priority,

            "focus":
                "Prioritize high-value "
                "opportunities with strong "
                "recovery probability.",

            "expected_recovery_label":
                _format_currency(
                    expected_recovery
                ),

            "opportunity_count":
                high_priority,
        },
    }