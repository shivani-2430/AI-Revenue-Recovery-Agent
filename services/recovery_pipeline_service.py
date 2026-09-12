from database.db import db
from models import Transaction, RecoveryAction, AuditLog
from ml.predict_recovery import predict_recovery_batch, calculate_revenue_at_risk
from services.mock_policies_service import evaluate_guardrails
from services.ai_strategy_service import generate_strategy
import hashlib
from datetime import datetime
from sqlalchemy.orm import joinedload


def _safe_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _decision_id(transaction_id):
    digest = hashlib.sha256(
        str(transaction_id).encode("utf-8")
    ).hexdigest()

    return f"DEC-{digest[:10].upper()}"


def _feature_row(transaction):
    customer = transaction.customer
    customer_value = _safe_float(customer.customer_value)

    customer_age_days = 0

    if customer.customer_since and transaction.transaction_timestamp:
        customer_age_days = max(
            0,
            (
                transaction.transaction_timestamp
                - customer.customer_since
            ).days
        )

    previous_recovery_success = 0

    for outcome in transaction.recovery_outcomes:
        if _safe_float(outcome.amount_recovered) > 0:
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
        "amount": _safe_float(transaction.amount),
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
            1 if customer_value >= 100000 else 0
        ),
        "previous_recovery_success": (
            previous_recovery_success
        ),
        "response_code": None,
    }


def process_recovery(transaction_id):
    transaction = (
        Transaction.query
        .options(
            joinedload(Transaction.customer),
            joinedload(Transaction.recovery_outcomes),
        )
        .filter_by(transaction_id=transaction_id)
        .first()
    )

    if not transaction:
        raise ValueError("Transaction not found.")

    if str(transaction.status).upper() != "FAILED":
        raise ValueError(
            "Recovery pipeline only processes failed transactions."
        )
    existing_action = (
        RecoveryAction.query
        .filter_by(transaction_id=transaction.id)
        .order_by(RecoveryAction.created_at.desc())
        .first()
    )

    if existing_action:
        return {
            "success": True,
            "duplicate": True,
            "transaction_id": transaction.transaction_id,
            "recovery_action_id": existing_action.id,
            "status": existing_action.status,
            "recommended_action": existing_action.action_type,
            "reason": existing_action.reason,
            "message": "Recovery decision already exists for this transaction."
        }

    features = _feature_row(transaction)

    prediction = predict_recovery_batch(
        [features]
    )[0]

    probability = _safe_float(
        prediction.get(
            "recovery_probability",
            0
        )
    )

    amount = _safe_float(
        transaction.amount
    )

    revenue_at_risk = calculate_revenue_at_risk(
        amount,
        probability
    )

    priority = (
        "HIGH"
        if probability >= 0.70
        else "MEDIUM"
        if probability >= 0.40
        else "LOW"
    )

    context = {
        "transaction_id": transaction.transaction_id,
        "customer_id": transaction.customer.customer_id,
        "customer_segment": transaction.customer.customer_segment,
        "amount": amount,
        "payment_method": transaction.payment_method,
        "merchant_category": transaction.merchant_category,
        "failure_reason": (
            transaction.failure_reason
            or "UNKNOWN"
        ),
        "retry_count": int(
            transaction.retry_count or 0
        ),
        "subscription_status": (
            transaction.subscription_status
            or "UNKNOWN"
        ),
        "recovery_probability": probability,
        "revenue_at_risk": revenue_at_risk,
    }

    strategy = generate_strategy(
        context,
        priority
    )

    if not isinstance(strategy, dict):
        strategy = {}

    final_strategy = strategy.get(
        "final_strategy",
        {}
    )

    if not isinstance(final_strategy, dict):
        final_strategy = {}

    recommended_action = (
        final_strategy.get(
            "recommended_action"
        )
        or final_strategy.get(
            "action"
        )
        or "CUSTOMER REMINDER"
    )

    reason = (
        final_strategy.get(
            "reason"
        )
        or final_strategy.get(
            "reasoning"
        )
        or (
            "AI recovery strategy generated "
            "from transaction context."
        )
    )

    guardrail = evaluate_guardrails(
        recovery_probability=probability * 100,
        retry_count=int(
            transaction.retry_count or 0
        ),
        amount=amount,
        payment_method=transaction.payment_method,
    )

    guardrail_status = guardrail.get(
        "status",
        "BLOCKED"
    )

    if guardrail_status == "APPROVED":
        action_status = "APPROVED"
    elif guardrail_status == "ESCALATED":
        action_status = "ESCALATED"
    else:
        action_status = "BLOCKED"

    action = RecoveryAction(
        transaction_id=transaction.id,
        action_type=str(
            recommended_action
        ),
        reason=str(reason),
        risk_score=round(
            1 - probability,
            4
        ),
        recovery_probability=round(
            probability,
            4
        ),
        revenue_at_risk=round(
            revenue_at_risk,
            2
        ),
        status=action_status,
        guardrail_status=guardrail_status,
        created_at=datetime.utcnow(),
    )

    db.session.add(action)
    db.session.flush()

    decision_id = _decision_id(
        transaction.transaction_id
    )

    audit = AuditLog(
        transaction_id=transaction.id,
        decision_id=decision_id,
        decision=action_status,
        reason=str(reason),
        policy_check=guardrail_status,
        action=str(recommended_action),
        result=(
            "READY_FOR_EXECUTION"
            if guardrail_status == "APPROVED"
            else guardrail_status
        ),
        model_version="Recovery Intelligence v1",
        created_at=datetime.utcnow(),
    )

    db.session.add(audit)
    db.session.commit()

    execution_result = None

    if action_status == "APPROVED":
        try:
            from services.recovery_execution_service import (
                execute_recovery
            )

            execution_result = execute_recovery(
                action.id
            )

        except Exception as error:
            db.session.rollback()

            execution_result = {
                "success": False,
                "executed": False,
                "error": str(error),
            }

    return {
        "success": True,
        "transaction_id": transaction.transaction_id,
        "decision_id": decision_id,
        "recovery_probability": round(
            probability,
            4
        ),
        "recovery_percentage": round(
            probability * 100,
            2
        ),
        "revenue_at_risk": round(
            revenue_at_risk,
            2
        ),
        "priority": priority,
        "recommended_action": str(
            recommended_action
        ),
        "reason": reason,
        "guardrail": guardrail,
        "status": action_status,
        "recovery_action_id": action.id,
        "execution": execution_result,
        "strategy": strategy,
    }
