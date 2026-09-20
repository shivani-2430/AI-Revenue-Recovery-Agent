from sqlalchemy.orm import joinedload

from models.audit_log import AuditLog
from models.transaction import Transaction


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
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_currency(value):
    amount = _safe_float(value)
    return f"\u20b9{amount:,.2f}"


def _get_latest_action(transaction):
    actions = list(
        getattr(
            transaction,
            "recovery_actions",
            [],
        )
        or []
    )

    if not actions:
        return None

    actions.sort(
        key=lambda item: (
            item.created_at is not None,
            item.created_at,
        ),
        reverse=True,
    )

    return actions[0]


def _get_recovered_amount(transaction):
    outcomes = list(
        getattr(
            transaction,
            "recovery_outcomes",
            [],
        )
        or []
    )

    total = 0.0

    for outcome in outcomes:
        total += _safe_float(
            outcome.amount_recovered
        )

    return total


def _normalize_guardrail(
    audit_log,
    recovery_action,
):
    guardrail_status = ""

    if recovery_action:
        guardrail_status = str(
            recovery_action.guardrail_status
            or ""
        ).strip()

    if guardrail_status:
        return guardrail_status.upper()

    policy_check = str(
        audit_log.policy_check
        or ""
    ).strip()

    if policy_check:
        return policy_check.upper()

    return "UNKNOWN"


def _normalize_status(
    audit_log,
    recovery_action,
):
    if recovery_action:
        action_status = str(
            recovery_action.status
            or ""
        ).strip()

        if action_status:
            return action_status.upper()

    result = str(
        audit_log.result
        or ""
    ).strip()

    if result:
        return result.upper()

    decision = str(
        audit_log.decision
        or ""
    ).strip()

    if decision:
        return decision.upper()

    return "UNKNOWN"


def _normalize_action(
    audit_log,
    recovery_action,
):
    if recovery_action:
        action_type = str(
            recovery_action.action_type
            or ""
        ).strip()

        if action_type:
            return action_type.upper()

    action = str(
        audit_log.action
        or ""
    ).strip()

    if action:
        return action.upper()

    return "UNKNOWN"


def _build_record(audit_log):
    transaction = audit_log.transaction

    if transaction is None:
        return None

    recovery_action = _get_latest_action(
        transaction
    )

    recovered_amount = (
        _get_recovered_amount(
            transaction
        )
    )

    amount = _safe_float(
        transaction.amount
    )

    customer = transaction.customer

    customer_id = ""

    if customer:
        customer_id = str(
            customer.customer_id
        )

    if recovery_action:
        recovery_probability = _safe_float(
            recovery_action.recovery_probability
        )
    else:
        recovery_probability = 0.0

    if recovery_probability <= 1:
        recovery_probability *= 100

    expected_recovery = (
        amount
        * recovery_probability
        / 100
    )

    decision_id = str(
        audit_log.decision_id
        or ""
    )

    model_version = (
        audit_log.model_version
        or "Recovery Intelligence v1"
    )

    guardrail = _normalize_guardrail(
        audit_log,
        recovery_action,
    )

    status = _normalize_status(
        audit_log,
        recovery_action,
    )

    action = _normalize_action(
        audit_log,
        recovery_action,
    )

    outcome = (
        "RECOVERED"
        if recovered_amount > 0
        else "NOT RECOVERED"
    )

    timestamp = ""

    if audit_log.created_at:
        timestamp = (
            audit_log.created_at.isoformat()
        )

    failure_reason = (
        transaction.failure_reason
        or "Unknown"
    )

    payment_method = (
        transaction.payment_method
        or "Unknown"
    )

    return {
        "decision_id": decision_id,

        "transaction_id": str(
            transaction.transaction_id
        ),

        "customer_id": customer_id,

        "timestamp": timestamp,

        "model": model_version,

        "decision_source": (
            "Recovery Decision Audit Log"
        ),

        "amount": amount,

        "amount_label": _format_currency(
            amount
        ),

        "amount_display": _format_currency(
            amount
        ),

        "revenue_at_risk": amount,

        "revenue_at_risk_label": (
            _format_currency(amount)
        ),

        "recovery_probability": round(
            recovery_probability,
            1,
        ),

        "confidence": round(
            recovery_probability,
            1,
        ),

        "expected_recovery": round(
            expected_recovery,
            2,
        ),

        "expected_recovery_label": (
            _format_currency(
                expected_recovery
            )
        ),

        "failure_reason": failure_reason,

        "payment_method": payment_method,

        "customer_segment": (
            customer.customer_segment
            if customer
            else "Unknown"
        ),

        "retry_count": _safe_int(
            transaction.retry_count
        ),

        "recommendation": action,

        "recommended_action": action,

        "guardrail": guardrail,

        "status": status,

        "outcome": outcome,

        "recovered_amount": round(
            recovered_amount,
            2,
        ),

        "recovered_amount_display": (
            _format_currency(
                recovered_amount
            )
        ),

        "policy": (
            audit_log.policy_check
            or "Recovery Policy v1"
        ),

        "explanation": (
            audit_log.reason
            or (
                "Decision recorded by "
                "the recovery decision pipeline."
            )
        ),

        "reason": (
            audit_log.reason
            or ""
        ),

        "audit_action": (
            audit_log.action
            or ""
        ),

        "audit_result": (
            audit_log.result
            or ""
        ),
    }


def get_audit_trail(
    search=None,
    status=None,
    action=None,
    guardrail=None,
    page=1,
    per_page=15,
):
    """
    Retrieve audit events directly from
    PostgreSQL AuditLog records.
    """

    audit_logs = (
        AuditLog.query
        .options(
            joinedload(
                AuditLog.transaction
            ).joinedload(
                Transaction.customer
            ),

            joinedload(
                AuditLog.transaction
            ).joinedload(
                Transaction.recovery_actions
            ),

            joinedload(
                AuditLog.transaction
            ).joinedload(
                Transaction.recovery_outcomes
            ),
        )
        .order_by(
            AuditLog.created_at.desc()
        )
        .all()
    )

    records = []

    for audit_log in audit_logs:
        record = _build_record(
            audit_log
        )

        if record is not None:
            records.append(record)

    search_value = str(
        search or ""
    ).strip().lower()

    if search_value:
        records = [
            record
            for record in records
            if (
                search_value
                in record[
                    "transaction_id"
                ].lower()

                or search_value
                in record[
                    "customer_id"
                ].lower()

                or search_value
                in record[
                    "decision_id"
                ].lower()

                or search_value
                in record[
                    "failure_reason"
                ].lower()

                or search_value
                in record[
                    "recommendation"
                ].lower()
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
        _safe_int(
            page,
            1,
        ),
        1,
    )

    per_page = max(
        min(
            _safe_int(
                per_page,
                15,
            ),
            100,
        ),
        1,
    )

    total_pages = max(
        (
            total
            + per_page
            - 1
        )
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
        record["status"]
        in {
            "APPROVED",
            "EXECUTED",
        }
        for record in records
    )

    blocked = sum(
        record["status"]
        == "BLOCKED"
        for record in records
    )

    escalated = sum(
        record["status"]
        == "ESCALATED"
        for record in records
    )

    revenue_at_risk = sum(
        record["revenue_at_risk"]
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
                _format_currency(
                    revenue_at_risk
                )
            ),

            "recovered_revenue_display": (
                _format_currency(
                    recovered_revenue
                )
            ),
        },

        "pagination": {
            "page": page,

            "per_page": per_page,

            "total": total,

            "total_pages": total_pages,
        },
    }