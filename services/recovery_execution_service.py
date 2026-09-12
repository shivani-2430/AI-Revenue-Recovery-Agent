from datetime import datetime

from database.db import db

from models.transaction import Transaction
from models.recovery_action import RecoveryAction
from models.recovery_outcome import RecoveryOutcome
from models.audit_log import AuditLog

from services.razorpay_service import (
    is_configured,
    create_payment_link,
)


def execute_recovery(recovery_action_id):

    action = RecoveryAction.query.get(
        recovery_action_id
    )

    if not action:
        return {
            "success": False,
            "error": "Recovery action not found."
        }

    transaction = Transaction.query.get(
        action.transaction_id
    )

    if not transaction:
        return {
            "success": False,
            "error": "Transaction not found."
        }

    existing_outcome = (
        RecoveryOutcome.query
        .filter_by(
            recovery_action_id=action.id
        )
        .first()
    )

    if existing_outcome:

        return {
            "success": True,
            "duplicate": True,
            "status": existing_outcome.outcome,
            "amount_recovered": float(
                existing_outcome.amount_recovered or 0
            )
        }

    if action.status != "APPROVED":

        action.status = "STOPPED"

        db.session.add(
            AuditLog(
                transaction_id=transaction.id,
                decision_id=str(action.id),
                decision=action.action_type,
                reason=action.reason,
                policy_check=action.guardrail_status,
                action="STOP",
                result="NOT_APPROVED",
                model_version="recoverai-v1"
            )
        )

        db.session.commit()

        return {
            "success": True,
            "status": "STOPPED",
            "reason": "Recovery action was not approved."
        }

    if not is_configured():

        action.status = "WAITING_FOR_RAZORPAY"

        db.session.add(
            AuditLog(
                transaction_id=transaction.id,
                decision_id=str(action.id),
                decision=action.action_type,
                reason=action.reason,
                policy_check=action.guardrail_status,
                action="CREATE_PAYMENT_LINK",
                result="WAITING_FOR_RAZORPAY",
                model_version="recoverai-v1"
            )
        )

        db.session.commit()

        return {
            "success": True,
            "executed": False,
            "status": "WAITING_FOR_RAZORPAY",
            "message": "Razorpay credentials are not configured."
        }

    reference_id = (
        f"REC-{transaction.transaction_id}"
    )[:40]

    customer = transaction.customer

    customer_name = None

    if customer:
        customer_name = customer.customer_id

    result = create_payment_link(
        amount=float(transaction.amount),
        reference_id=reference_id,
        customer_name=customer_name,
        description=(
            "RecoverAI payment recovery for "
            f"{transaction.transaction_id}"
        ),
        notes={
            "transaction_id": str(
                transaction.transaction_id
            ),
            "recovery_action_id": str(
                action.id
            ),
            "source": "RecoverAI"
        }
    )

    if not result.get("success"):

        action.status = "EXECUTION_FAILED"

        db.session.add(
            AuditLog(
                transaction_id=transaction.id,
                decision_id=str(action.id),
                decision=action.action_type,
                reason=action.reason,
                policy_check=action.guardrail_status,
                action="CREATE_PAYMENT_LINK",
                result="FAILED",
                model_version="recoverai-v1"
            )
        )

        db.session.commit()

        return {
            "success": False,
            "executed": False,
            "status": "EXECUTION_FAILED",
            "error": result.get(
                "error",
                "Unable to create payment link."
            )
        }

    payment_link = result["payment_link"]

    action.status = "EXECUTED"
    action.executed_at = datetime.utcnow()

    db.session.add(
        AuditLog(
            transaction_id=transaction.id,
            decision_id=str(action.id),
            decision=action.action_type,
            reason=action.reason,
            policy_check=action.guardrail_status,
            action="CREATE_PAYMENT_LINK",
            result="PAYMENT_LINK_CREATED",
            model_version="recoverai-v1"
        )
    )

    db.session.commit()

    return {
        "success": True,
        "executed": True,
        "status": "PAYMENT_LINK_CREATED",
        "payment_link_id": payment_link.get("id"),
        "payment_link_url": payment_link.get("short_url"),
        "amount": float(transaction.amount),
        "reference_id": reference_id
    }