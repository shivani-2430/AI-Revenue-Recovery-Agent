from math import ceil
from pathlib import Path

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from database.db import db
from models import Transaction, Customer
from ml.predict_recovery import predict_recovery_batch


BASE_DIR = Path(__file__).resolve().parent.parent


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


def _format_currency(amount):
    amount = _safe_float(amount)

    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f}Cr"

    if amount >= 100_000:
        return f"₹{amount / 100_000:.2f}L"

    if amount >= 1_000:
        return f"₹{amount / 1_000:.1f}K"

    return f"₹{amount:,.0f}"


def _decision_id(transaction_id):
    transaction_id = _safe_string(transaction_id, "UNKNOWN")
    return f"DEC-{transaction_id}"


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

    total_payments = (
        successful_payments
        + failed_payments
    )

    previous_recovery_success = int(
        successful_payments > 0
    )

    high_value_customer = int(
        customer_value >= 100000
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
            "Unknown",
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
        "previous_recovery_success": previous_recovery_success,
        "high_value_customer": high_value_customer,
    }
def _recommended_action(
    failure_reason,
    probability,
    retry_count,
):
    reason = _safe_string(
        failure_reason
    ).lower()

    probability = _safe_float(probability)
    retry_count = _safe_int(retry_count)

    if probability < 35:
        return "STOP"

    if retry_count >= 3:
        return "CUSTOMER REMINDER"

    if "network" in reason or "timeout" in reason:
        return "SMART RETRY"

    if "authentication" in reason:
        return "AUTHENTICATION RETRY"

    if "insufficient" in reason:
        return "CUSTOMER REMINDER"

    if "bank" in reason:
        return "PAYMENT RETRY"

    return "SMART RETRY"


def _guardrail(
    probability,
    retry_count,
    amount,
):
    probability = _safe_float(probability)
    retry_count = _safe_int(retry_count)
    amount = _safe_float(amount)

    if probability < 35:
        return "BLOCKED"

    if retry_count >= 3:
        return "REVIEW"

    if amount >= 500_000:
        return "REVIEW"

    return "PASSED"


def _decision_status(
    action,
    guardrail,
):
    if guardrail == "BLOCKED":
        return "BLOCKED"

    if guardrail == "REVIEW":
        return "ESCALATED"

    if action == "STOP":
        return "BLOCKED"

    return "APPROVED"


def _confidence(
    probability,
    historical_success_rate,
):
    probability = _safe_float(probability)
    historical_rate = _safe_float(
        historical_success_rate
    )

    if historical_rate <= 1:
        historical_rate *= 100

    confidence = (
        probability * 0.75
        + historical_rate * 0.25
    )

    return round(
        max(
            0,
            min(
                100,
                confidence,
            ),
        ),
        1,
    )


def _decision_reasons(
    transaction,
    probability,
):
    reasons = []

    probability = _safe_float(probability)

    amount = _safe_float(
        transaction.amount
    )

    retry_count = _safe_int(
        transaction.retry_count
    )

    historical_rate = _safe_float(
        transaction.customer.historical_success_rate
    )

    if historical_rate <= 1:
        historical_rate *= 100

    failure_reason = _safe_string(
        transaction.failure_reason,
        "Unknown",
    )

    if probability >= 70:
        reasons.append(
            "High recovery probability"
        )
    elif probability >= 45:
        reasons.append(
            "Moderate recovery probability"
        )
    else:
        reasons.append(
            "Low recovery probability"
        )

    if historical_rate >= 70:
        reasons.append(
            "Strong historical payment performance"
        )
    elif historical_rate > 0:
        reasons.append(
            "Historical payment behavior considered"
        )

    if retry_count == 0:
        reasons.append(
            "No previous retry attempt detected"
        )
    elif retry_count < 3:
        reasons.append(
            f"{retry_count} previous retry attempt(s)"
        )
    else:
        reasons.append(
            "Retry threshold requires review"
        )

    if amount >= 100_000:
        reasons.append(
            "Material revenue exposure"
        )

    reason_lower = failure_reason.lower()

    if (
        "network" in reason_lower
        or "timeout" in reason_lower
    ):
        reasons.append(
            "Failure pattern indicates a potentially temporary issue"
        )

    return reasons[:4]


def _build_decision(
    transaction,
    probability,
):
    amount = _safe_float(
        transaction.amount
    )

    retry_count = _safe_int(
        transaction.retry_count
    )

    historical_rate = _safe_float(
        transaction.customer.historical_success_rate
    )

    if historical_rate <= 1:
        historical_rate *= 100

    action = _recommended_action(
        transaction.failure_reason,
        probability,
        retry_count,
    )

    guardrail = _guardrail(
        probability,
        retry_count,
        amount,
    )

    status = _decision_status(
        action,
        guardrail,
    )

    confidence = _confidence(
        probability,
        historical_rate,
    )

    revenue_at_risk = amount

    expected_recovery = (
        amount
        * probability
        / 100
    )

    failure_reason = _safe_string(
        transaction.failure_reason,
        "Unknown",
    )

    if action == "SMART RETRY":
        explanation = (
            "The recovery model indicates meaningful "
            "recovery potential and the failure profile "
            "is suitable for a controlled retry."
        )
    elif action == "CUSTOMER REMINDER":
        explanation = (
            "The recovery policy favors customer intervention "
            "instead of another automatic payment attempt."
        )
    elif action == "PAYMENT RETRY":
        explanation = (
            "The recovery profile supports another "
            "controlled payment attempt."
        )
    elif action == "AUTHENTICATION RETRY":
        explanation = (
            "The payment failure requires an "
            "authentication-aware recovery path."
        )
    else:
        explanation = (
            "The predicted recovery value does not "
            "justify automatic intervention under "
            "the current policy."
        )

    if guardrail == "PASSED":
        policy = (
            "Recovery policy permits controlled action"
        )
    elif guardrail == "REVIEW":
        policy = (
            "Additional policy review required"
        )
    else:
        policy = (
            "Automatic recovery blocked by policy"
        )

    return {
        "decision_id": _decision_id(
            transaction.transaction_id
        ),
        "transaction_id": _safe_string(
            transaction.transaction_id
        ),
        "customer_id": _safe_string(
            transaction.customer.customer_id
        ),
        "customer_segment": _safe_string(
            transaction.customer.customer_segment,
            "STANDARD",
        ),
        "amount": round(
            amount,
            2,
        ),
        "amount_label": _format_currency(
            amount
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
        "payment_method": _safe_string(
            transaction.payment_method,
            "Unknown",
        ),
        "failure_reason": failure_reason,
        "recovery_probability": round(
            _safe_float(probability),
            1,
        ),
        "confidence": confidence,
        "retry_count": retry_count,
        "recommended_action": action,
        "guardrail": guardrail,
        "status": status,
        "policy": policy,
        "explanation": explanation,
        "reasons": _decision_reasons(
            transaction,
            probability,
        ),
        "model": "Recovery Intelligence v1",
        "decision_source": "ML Recovery Decision Pipeline",
        "timestamp": _safe_string(
            transaction.transaction_timestamp
        ),
    }


def get_ai_decisions(
    search=None,
    status=None,
    action=None,
    guardrail=None,
    page=1,
    per_page=10,
):
    query = (
        Transaction.query
        .options(
            joinedload(Transaction.customer)
        )
        .filter(
            Transaction.status.ilike("FAILED")
        )
    )

    if search:
        search_value = f"%{str(search).strip()}%"

        query = query.filter(
            or_(
                Transaction.transaction_id.ilike(
                    search_value
                ),
                Transaction.failure_reason.ilike(
                    search_value
                ),
                Transaction.payment_method.ilike(
                    search_value
                ),
                Transaction.customer.has(
                    Customer.customer_id.ilike(
                        search_value
                    )
                ),
            )
        )

    transactions = query.all()

    if not transactions:
        return {
            "summary": {
                "total": 0,
                "total_label": "0",
                "approved": 0,
                "approved_label": "0",
                "blocked": 0,
                "blocked_label": "0",
                "escalated": 0,
                "escalated_label": "0",
                "revenue_at_risk": 0,
                "revenue_at_risk_label": "₹0",
                "expected_recovery": 0,
                "expected_recovery_label": "₹0",
                "average_confidence": 0,
            },
            "decisions": [],
            "pagination": {
                "page": 1,
                "per_page": max(1, min(50, _safe_int(per_page, 10))),
                "total": 0,
                "total_pages": 1,
            },
        }

    feature_rows = [
        _feature_row(transaction)
        for transaction in transactions
    ]

    predictions = predict_recovery_batch(
        feature_rows
    )

    decisions = [
        _build_decision(
            transaction,
            prediction["recovery_percentage"],
        )
        for transaction, prediction
        in zip(
            transactions,
            predictions,
        )
    ]

    if status:
        status_value = str(
            status
        ).strip().upper()

        decisions = [
            item
            for item in decisions
            if item["status"] == status_value
        ]

    if action:
        action_value = str(
            action
        ).strip().upper()

        decisions = [
            item
            for item in decisions
            if item["recommended_action"]
            == action_value
        ]

    if guardrail:
        guardrail_value = str(
            guardrail
        ).strip().upper()

        decisions = [
            item
            for item in decisions
            if item["guardrail"]
            == guardrail_value
        ]

    decisions.sort(
        key=lambda item: (
            {
                "APPROVED": 3,
                "ESCALATED": 2,
                "BLOCKED": 1,
            }.get(
                item["status"],
                0,
            ),
            item["expected_recovery"],
            item["confidence"],
        ),
        reverse=True,
    )

    total = len(decisions)

    approved = sum(
        item["status"] == "APPROVED"
        for item in decisions
    )

    blocked = sum(
        item["status"] == "BLOCKED"
        for item in decisions
    )

    escalated = sum(
        item["status"] == "ESCALATED"
        for item in decisions
    )

    revenue_at_risk = sum(
        item["revenue_at_risk"]
        for item in decisions
    )

    expected_recovery = sum(
        item["expected_recovery"]
        for item in decisions
    )

    average_confidence = (
        sum(
            item["confidence"]
            for item in decisions
        )
        / total
        if total
        else 0
    )

    per_page = max(
        1,
        min(
            50,
            _safe_int(
                per_page,
                10,
            ),
        ),
    )

    page = max(
        1,
        _safe_int(
            page,
            1,
        ),
    )

    total_pages = max(
        1,
        ceil(
            total / per_page
        ),
    )

    page = min(
        page,
        total_pages,
    )

    start = (
        page - 1
    ) * per_page

    end = (
        start
        + per_page
    )

    paginated = decisions[
        start:end
    ]

    return {
        "summary": {
            "total": total,
            "total_label": f"{total:,}",
            "approved": approved,
            "approved_label": f"{approved:,}",
            "blocked": blocked,
            "blocked_label": f"{blocked:,}",
            "escalated": escalated,
            "escalated_label": f"{escalated:,}",
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
            "average_confidence": round(
                average_confidence,
                1,
            ),
        },
        "decisions": paginated,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }