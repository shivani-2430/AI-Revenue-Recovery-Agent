import os
import hmac
import hashlib
from datetime import datetime

from dotenv import load_dotenv

from database.db import db
from models import (
    Customer,
    Transaction,
    PaymentAttempt,
    RecoveryAction,
    RecoveryOutcome,
    AuditLog
)

load_dotenv()


def verify_signature(payload, signature):
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    if not secret:
        return True

    if not signature:
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        expected,
        signature
    )


def _get_payment_payload(payload):
    return (
        payload.get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )


def _map_status(event):
    event = str(event or "").lower()

    if event in {
        "payment.captured",
        "payment.authorized"
    }:
        return "SUCCESS"

    if event in {
        "payment.failed",
        "payment.cancelled"
    }:
        return "FAILED"

    return "UNKNOWN"


def _update_recovery_outcome(transaction, status, amount):
    action = (
        RecoveryAction.query
        .filter_by(transaction_id=transaction.id)
        .order_by(RecoveryAction.created_at.desc())
        .first()
    )

    if not action:
        return None

    outcome = (
        RecoveryOutcome.query
        .filter_by(
            recovery_action_id=action.id
        )
        .first()
    )

    if status == "SUCCESS":
        recovered_amount = amount

        if not outcome:
            outcome = RecoveryOutcome(
                transaction_id=transaction.id,
                recovery_action_id=action.id,
                outcome="SUCCESS",
                amount_recovered=recovered_amount,
                completed_at=datetime.utcnow()
            )
            db.session.add(outcome)
        else:
            outcome.outcome = "SUCCESS"
            outcome.amount_recovered = recovered_amount
            outcome.completed_at = datetime.utcnow()

        action.status = "EXECUTED"

        if not action.executed_at:
            action.executed_at = datetime.utcnow()

        audit = AuditLog(
            transaction_id=transaction.id,
            decision_id=f"OUTCOME-{action.id}",
            decision="RECOVERY_SUCCESS",
            reason="Razorpay payment was successfully captured.",
            policy_check=action.guardrail_status,
            action=action.action_type,
            result="SUCCESS",
            model_version="Recovery Intelligence v1",
            created_at=datetime.utcnow()
        )

        db.session.add(audit)

        return {
            "outcome": "SUCCESS",
            "amount_recovered": recovered_amount
        }

    if status == "FAILED":
        if outcome:
            outcome.outcome = "FAILED"
            outcome.amount_recovered = 0
            outcome.completed_at = datetime.utcnow()
        else:
            outcome = RecoveryOutcome(
                transaction_id=transaction.id,
                recovery_action_id=action.id,
                outcome="FAILED",
                amount_recovered=0,
                completed_at=datetime.utcnow()
            )
            db.session.add(outcome)

        action.status = "RECOVERY_FAILED"

        audit = AuditLog(
            transaction_id=transaction.id,
            decision_id=f"OUTCOME-{action.id}",
            decision="RECOVERY_FAILED",
            reason=(
                transaction.failure_reason
                or "Razorpay recovery attempt failed."
            ),
            policy_check=action.guardrail_status,
            action=action.action_type,
            result="FAILED",
            model_version="Recovery Intelligence v1",
            created_at=datetime.utcnow()
        )

        db.session.add(audit)

        return {
            "outcome": "FAILED",
            "amount_recovered": 0
        }

    return None


def process_webhook(payload):
    event = payload.get(
        "event",
        "unknown"
    )

    payment = _get_payment_payload(
        payload
    )

    razorpay_payment_id = payment.get(
        "id"
    )

    if not razorpay_payment_id:
        raise ValueError(
            "Razorpay payment ID is missing."
        )

    status = _map_status(event)

    if status == "UNKNOWN":
        return {
            "processed": False,
            "event": event,
            "payment_id": razorpay_payment_id,
            "message": "Unsupported Razorpay event."
        }

    amount = (
        float(payment.get("amount", 0))
        / 100
    )

    method = str(
        payment.get(
            "method",
            "UNKNOWN"
        )
    ).upper()

    error_description = payment.get(
        "error_description"
    )

    notes = payment.get(
        "notes"
    ) or {}

    customer_id_value = (
        notes.get("customer_id")
        or payment.get("email")
        or payment.get("contact")
        or f"razorpay_{razorpay_payment_id}"
    )

    merchant_category = (
        notes.get("merchant_category")
        or "GENERAL"
    )

    customer = (
        Customer.query
        .filter_by(
            customer_id=str(
                customer_id_value
            )
        )
        .first()
    )

    if not customer:
        customer = Customer(
            customer_id=str(
                customer_id_value
            ),
            customer_segment="STANDARD",
            customer_since=datetime.utcnow(),
            successful_payments=0,
            failed_payments=0,
            historical_success_rate=0.0,
            customer_value=amount
        )

        db.session.add(customer)
        db.session.flush()

    transaction = (
        Transaction.query
        .filter_by(
            transaction_id=razorpay_payment_id
        )
        .first()
    )

    is_new_transaction = transaction is None

    if not transaction:
        transaction = Transaction(
            transaction_id=razorpay_payment_id,
            customer_id=customer.id,
            amount=amount,
            payment_method=method,
            merchant_category=merchant_category,
            status=status,
            failure_reason=error_description,
            transaction_timestamp=datetime.utcnow(),
            subscription_status=notes.get(
                "subscription_status"
            ),
            retry_count=0
        )

        db.session.add(transaction)
        db.session.flush()

    else:
        previous_status = transaction.status

        transaction.status = status
        transaction.failure_reason = (
            error_description
        )
        transaction.payment_method = method

        if (
            previous_status == "FAILED"
            and status == "SUCCESS"
        ):
            transaction.failure_reason = None

    latest_attempt = (
        PaymentAttempt.query
        .filter_by(
            transaction_id=transaction.id
        )
        .order_by(
            PaymentAttempt.attempt_number.desc()
        )
        .first()
    )

    attempt_number = (
        latest_attempt.attempt_number + 1
        if latest_attempt
        else 1
    )

    attempt = PaymentAttempt(
        transaction_id=transaction.id,
        attempt_number=attempt_number,
        attempted_at=datetime.utcnow(),
        status=status,
        failure_reason=error_description,
        response_code=payment.get(
            "error_code"
        )
    )

    db.session.add(attempt)

    transaction.retry_count = max(
        0,
        attempt_number - 1
    )

    if is_new_transaction:
        if status == "SUCCESS":
            customer.successful_payments = 1
        elif status == "FAILED":
            customer.failed_payments = 1
    else:
        customer.successful_payments = int(
            customer.successful_payments or 0
        )

        customer.failed_payments = int(
            customer.failed_payments or 0
        )

    total_payments = (
        customer.successful_payments
        + customer.failed_payments
    )

    customer.historical_success_rate = (
        round(
            customer.successful_payments
            / total_payments,
            4
        )
        if total_payments
        else 0.0
    )

    db.session.commit()

    recovery_result = None

    if status == "FAILED":
        try:
            from services.recovery_pipeline_service import (
                process_recovery
            )

            recovery_result = process_recovery(
                transaction.transaction_id
            )

        except Exception as error:
            db.session.rollback()

            recovery_result = {
                "success": False,
                "error": str(error)
            }

    elif status == "SUCCESS":
        try:
            recovery_result = (
                _update_recovery_outcome(
                    transaction,
                    status,
                    amount
                )
            )

            db.session.commit()

        except Exception as error:
            db.session.rollback()

            recovery_result = {
                "success": False,
                "error": str(error)
            }

    return {
        "processed": True,
        "event": event,
        "payment_id": razorpay_payment_id,
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "amount": amount,
        "customer_id": customer.customer_id,
        "payment_attempt": attempt.attempt_number,
        "recovery_pipeline": recovery_result
    }
