import hashlib

from sqlalchemy.orm import joinedload

from models.transaction import Transaction
from models.recovery_action import RecoveryAction
from models.recovery_outcome import RecoveryOutcome
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


def _decision_id(transaction_id):
    digest = hashlib.sha256(
        str(transaction_id).encode("utf-8")
    ).hexdigest()

    return f"DEC-{digest[:10].upper()}"


def _feature_row(transaction):
    customer = transaction.customer

    customer_value = _safe_float(
        customer.customer_value
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

    previous_recovery_success = 0

    for outcome in transaction.recovery_outcomes:
        if _safe_float(
            outcome.amount_recovered
        ) > 0:
            previous_recovery_success = 1
            break

    return {
        "customer_segment": customer.customer_segment,
        "customer_age_days": customer_age_days,
        "successful_payments": int(
            customer.successful_payments or 0
        ),
        "failed_payments": int(
            customer.failed_payments or 0
        ),
        "historical_success_rate": _safe_float(
            customer.historical_success_rate
        ),
        "customer_value": customer_value,
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
        "hour": (
            transaction.transaction_timestamp.hour
            if transaction.transaction_timestamp
            else 12
        ),
        "day_of_week": (
            transaction.transaction_timestamp.weekday()
            if transaction.transaction_timestamp
            else 0
        ),
        "failure_reason": (
            transaction.failure_reason
            or "UNKNOWN"
        ),
        "high_value_customer": (
            1
            if customer_value >= 100000
            else 0
        ),
        "previous_recovery_success": (
            previous_recovery_success
        ),
        "response_code": None,
    }


def _derive_action(transaction, probability):
    reason = str(
        transaction.failure_reason or ""
    ).lower()

    retry_count = int(
        transaction.retry_count or 0
    )

    if retry_count >= 3:
        return "ESCALATION"

    if (
        "insufficient" in reason
        or "fund" in reason
    ):
        return "PAYMENT LINK"

    if (
        "expired" in reason
        or "timeout" in reason
    ):
        return "SMART RETRY"

    if probability >= 70:
        return "SMART RETRY"

    if probability >= 45:
        return "PAYMENT LINK"

    return "CUSTOMER REMINDER"


def _derive_guardrail(
    transaction,
    probability,
):
    retry_count = int(
        transaction.retry_count or 0
    )

    amount = _safe_float(
        transaction.amount
    )

    if retry_count >= 3:
        return "RETRY LIMIT"

    if amount > 100000:
        return "HIGH VALUE REVIEW"

    if probability < 40:
        return "LOW RECOVERY PROBABILITY"

    return "PASSED"


def _derive_status(guardrail):
    if guardrail == "PASSED":
        return "APPROVED"

    if guardrail == "HIGH VALUE REVIEW":
        return "ESCALATED"

    return "BLOCKED"


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

    amounts = {}

    for outcome in outcomes:
        transaction_id = outcome.transaction_id

        amounts[transaction_id] = (
            amounts.get(transaction_id, 0.0)
            + _safe_float(
                outcome.amount_recovered
            )
        )

    return amounts


def _build_record(
    transaction,
    probability,
    recovery_amount,
):
    transaction_id = str(
        transaction.transaction_id
    )

    amount = _safe_float(
        transaction.amount
    )

    customer_id = str(
        transaction.customer.customer_id
    )

    action = _derive_action(
        transaction,
        probability,
    )

    guardrail = _derive_guardrail(
        transaction,
        probability,
    )

    status = _derive_status(
        guardrail
    )

    return {
        "decision_id": _decision_id(
            transaction_id
        ),
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "timestamp": (
            transaction.transaction_timestamp.isoformat()
            if transaction.transaction_timestamp
            else ""
        ),
        "model": "Recovery Intelligence v1",
        "decision_source": (
            "Recovery decision pipeline"
        ),
        "recovery_probability": round(
            probability,
            1,
        ),
        "amount": amount,
        "amount_display": (
            f"₹{amount:,.2f}"
        ),
        "failure_reason": (
            transaction.failure_reason
            or "Unknown"
        ),
        "retry_count": int(
            transaction.retry_count or 0
        ),
        "recommendation": action,
        "guardrail": guardrail,
        "status": status,
        "outcome": (
            "RECOVERED"
            if recovery_amount > 0
            else "NOT RECOVERED"
        ),
        "recovered_amount": recovery_amount,
        "recovered_amount_display": (
            f"₹{recovery_amount:,.2f}"
        ),
        "policy": "Recovery Policy v1",
    }


def get_audit_trail(
    search=None,
    status=None,
    action=None,
    guardrail=None,
    page=1,
    per_page=15,
):
    transactions = (
        Transaction.query
        .options(
            joinedload(Transaction.customer),
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

    if not transactions:
        return {
            "records": [],
            "summary": {
                "total_events": 0,
                "approved": 0,
                "blocked": 0,
                "escalated": 0,
                "revenue_at_risk": 0,
                "recovered_revenue": 0,
                "revenue_at_risk_display": "₹0.00",
                "recovered_revenue_display": "₹0.00",
            },
            "pagination": {
                "page": 1,
                "per_page": per_page,
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

    recovery_amounts = _get_recovery_amounts(
        transactions
    )

    records = []

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

        records.append(
            _build_record(
                transaction,
                probability,
                recovery_amounts.get(
                    transaction.id,
                    0.0,
                ),
            )
        )

    search_value = str(
        search or ""
    ).strip().lower()

    if search_value:
        records = [
            record
            for record in records
            if (
                search_value
                in record["transaction_id"].lower()
                or search_value
                in record["customer_id"].lower()
                or search_value
                in record["decision_id"].lower()
                or search_value
                in record["failure_reason"].lower()
            )
        ]

    if status:
        status_value = str(
            status
        ).strip().upper()

        records = [
            record
            for record in records
            if record["status"]
            == status_value
        ]

    if action:
        action_value = str(
            action
        ).strip().upper()

        records = [
            record
            for record in records
            if record["recommendation"]
            == action_value
        ]

    if guardrail:
        guardrail_value = str(
            guardrail
        ).strip().upper()

        records = [
            record
            for record in records
            if record["guardrail"]
            == guardrail_value
        ]

    total = len(records)

    page = max(
        _safe_int(page, 1),
        1,
    )

    per_page = max(
        min(
            _safe_int(per_page, 15),
            100,
        ),
        1,
    )

    total_pages = max(
        (total + per_page - 1)
        // per_page,
        1,
    )

    if page > total_pages:
        page = total_pages

    start = (
        page - 1
    ) * per_page

    page_records = records[
        start:start + per_page
    ]

    approved = sum(
        record["status"] == "APPROVED"
        for record in records
    )

    blocked = sum(
        record["status"] == "BLOCKED"
        for record in records
    )

    escalated = sum(
        record["status"] == "ESCALATED"
        for record in records
    )

    revenue_at_risk = sum(
        record["amount"]
        for record in records
    )

    recovered_revenue = sum(
        record["recovered_amount"]
        for record in records
    )

    return {
        "records": page_records,
        "summary": {
            "total_events": total,
            "approved": approved,
            "blocked": blocked,
            "escalated": escalated,
            "revenue_at_risk": round(
                revenue_at_risk,
                2,
            ),
            "recovered_revenue": round(
                recovered_revenue,
                2,
            ),
            "revenue_at_risk_display": (
                f"₹{revenue_at_risk:,.2f}"
            ),
            "recovered_revenue_display": (
                f"₹{recovered_revenue:,.2f}"
            ),
        },
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }