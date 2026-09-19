from database.db import db

from models.transaction import Transaction
from models.customer import Customer
from models.recovery_action import RecoveryAction
from models.recovery_outcome import RecoveryOutcome
from models.payment_attempt import PaymentAttempt
from models.audit_log import AuditLog


def get_transaction_details(transaction_id):

    # =========================================================
    # FIND TRANSACTION
    # =========================================================

    original_transaction_id = str(
        transaction_id
    ).strip()

    transaction = (
        Transaction.query
        .filter(
            Transaction.transaction_id
            == original_transaction_id
        )
        .first()
    )

    if not transaction:
        return None

    # =========================================================
    # CUSTOMER
    # =========================================================

    customer = transaction.customer

    customer_id = (
        customer.customer_id
        if customer
        else None
    )

    # Customer model does not contain a customer_name field.
    # Use customer_id as the available customer identifier.
    customer_name = customer_id

    # Convert stored customer value into a readable segment.
    if customer:

        if customer.customer_segment:
            customer_value = (
                customer.customer_segment
            )

        elif float(
            customer.customer_value or 0
        ) >= 30000:

            customer_value = "High"

        elif float(
            customer.customer_value or 0
        ) >= 12000:

            customer_value = "Medium"

        else:

            customer_value = "Low"

    else:

        customer_value = "Unknown"

    # =========================================================
    # RECOVERY ACTION
    # =========================================================

    latest_action = None

    if transaction.recovery_actions:

        latest_action = max(
            transaction.recovery_actions,
            key=lambda action: (
                action.created_at
                or transaction.transaction_timestamp
            )
        )

    # =========================================================
    # RECOVERY OUTCOME
    # =========================================================

    recovery_outcome = None

    if latest_action:

        recovery_outcome = (
            latest_action.recovery_outcome
        )

    if not recovery_outcome and transaction.recovery_outcomes:

        recovery_outcome = max(
            transaction.recovery_outcomes,
            key=lambda outcome: (
                outcome.completed_at
                or transaction.transaction_timestamp
            )
        )

    # =========================================================
    # RECOVERY VALUES
    # =========================================================

    if latest_action:

        recovery_probability = (
            round(
                float(
                    latest_action.recovery_probability
                ) * 100,
                2
            )
            if latest_action.recovery_probability
            is not None
            else None
        )

        recovery_action = (
            latest_action.action_type
        )

        guardrail = (
            latest_action.guardrail_status
            or "PENDING"
        )

        revenue_at_risk = float(
            latest_action.revenue_at_risk
            or 0
        )

        risk_score = (
            float(
                latest_action.risk_score
            )
            if latest_action.risk_score
            is not None
            else None
        )

        action_reason = (
            latest_action.reason
        )

    else:

        recovery_probability = None
        recovery_action = None
        guardrail = "NOT_EVALUATED"
        revenue_at_risk = 0
        risk_score = None
        action_reason = None

    # =========================================================
    # OUTCOME VALUES
    # =========================================================

    amount_recovered = 0
    recovered_at = None

    if recovery_outcome:

        amount_recovered = float(
            recovery_outcome.amount_recovered
            or 0
        )

        recovered_at = (
            recovery_outcome.completed_at
        )

    # =========================================================
    # STATUS
    # =========================================================

    transaction_status = str(
        transaction.status or ""
    ).upper()

    if recovery_outcome:

        outcome_status = str(
            recovery_outcome.outcome or ""
        ).upper()

        if outcome_status == "SUCCESS":

            display_status = "RECOVERED"

        else:

            display_status = outcome_status

    elif transaction_status == "SUCCESS":

        display_status = "RECOVERED"

    elif transaction_status == "FAILED":

        if (
            transaction.retry_count is not None
            and transaction.retry_count < 3
        ):

            display_status = "RECOVERABLE"

        else:

            display_status = "FAILED"

    else:

        display_status = transaction_status

    # =========================================================
    # FAILURE PATTERN
    # =========================================================

    failure_reason = (
        transaction.failure_reason
        or "Unknown"
    )

    failure_reason_upper = (
        failure_reason.upper()
    )

    if (
        "NETWORK" in failure_reason_upper
        or "GATEWAY" in failure_reason_upper
    ):

        failure_pattern = "Temporary"

    elif "BANK" in failure_reason_upper:

        failure_pattern = (
            "Potentially Temporary"
        )

    elif (
        "INSUFFICIENT" in failure_reason_upper
        or "FUNDS" in failure_reason_upper
    ):

        failure_pattern = "Customer Funds"

    elif "AUTHENTICATION" in failure_reason_upper:

        failure_pattern = "Authentication"

    else:

        failure_pattern = "Unknown"

    # =========================================================
    # PAYMENT ATTEMPTS
    # =========================================================

    attempts = sorted(
        transaction.payment_attempts or [],
        key=lambda attempt: (
            attempt.attempt_number
            or 0
        )
    )

    latest_attempt = (
        attempts[-1]
        if attempts
        else None
    )

    attempt_id = None

    if latest_attempt:

        attempt_id = (
            f"ATT_{latest_attempt.id:06d}"
        )

    # =========================================================
    # AUDIT LOG
    # =========================================================

    audit_logs = sorted(
        transaction.audit_logs or [],
        key=lambda log: (
            log.created_at
            or transaction.transaction_timestamp
        )
    )

    latest_audit = (
        audit_logs[-1]
        if audit_logs
        else None
    )

    decision_id = (
        latest_audit.decision_id
        if latest_audit
        else None
    )

    policy = (
        latest_audit.policy_check
        if latest_audit
        else None
    )

    model = (
        latest_audit.model_version
        if latest_audit
        else "Recovery-RF-v1.0"
    )

    # =========================================================
    # PAYMENT TYPE
    # =========================================================

    payment_type = (
        "Subscription"
        if transaction.subscription_status
        else "One-time"
    )

    # =========================================================
    # RECOVERY TIME
    # =========================================================

    recovery_time = None

    if (
        latest_action
        and latest_action.executed_at
        and recovered_at
    ):

        recovery_time = int(
            (
                recovered_at
                - latest_action.executed_at
            ).total_seconds()
        )

    recovery_time_label = (
        f"{recovery_time} seconds"
        if recovery_time is not None
        else "Pending"
    )

    # =========================================================
    # TIMELINE
    # =========================================================

    timeline = []

    created_at = (
        transaction.transaction_timestamp
    )

    # ---------------------------------------------------------
    # PAYMENT INITIATED
    # ---------------------------------------------------------

    timeline.append(
        {
            "time":
                created_at.strftime(
                    "%I:%M:%S %p"
                ),

            "title":
                "Payment Initiated",

            "description":
                (
                    f"Customer started "
                    f"{transaction.payment_method} payment"
                ),

            "status":
                "COMPLETED",

            "type":
                "completed",

            "icon":
                "fa-play",
        }
    )

    # ---------------------------------------------------------
    # PAYMENT ATTEMPTS
    # ---------------------------------------------------------

    for attempt in attempts:

        attempt_status = str(
            attempt.status or ""
        ).upper()

        if attempt_status == "SUCCESS":

            timeline_type = "recovered"
            timeline_icon = "fa-check"

        elif attempt_status in {
            "FAILED",
            "FAILURE",
        }:

            timeline_type = "failed"
            timeline_icon = "fa-exclamation"

        else:

            timeline_type = "completed"
            timeline_icon = "fa-rotate"

        attempt_failure = (
            attempt.failure_reason
            or attempt_status
            or "Payment attempt processed"
        )

        timeline.append(
            {
                "time":
                    attempt.attempted_at.strftime(
                        "%I:%M:%S %p"
                    )
                    if attempt.attempted_at
                    else "",

                "title":
                    (
                        f"Payment Attempt "
                        f"#{attempt.attempt_number}"
                    ),

                "description":
                    str(attempt_failure),

                "status":
                    attempt_status,

                "type":
                    timeline_type,

                "icon":
                    timeline_icon,
            }
        )

    # ---------------------------------------------------------
    # ML ANALYSIS
    # ---------------------------------------------------------

    if latest_action:

        timeline.append(
            {
                "time":
                    (
                        latest_action.created_at.strftime(
                            "%I:%M:%S %p"
                        )
                        if latest_action.created_at
                        else ""
                    ),

                "title":
                    "ML Recovery Analysis",

                "description":
                    (
                        "Recovery probability calculated: "
                        f"{recovery_probability}%"
                    ),

                "status":
                    "ANALYZED",

                "type":
                    "intelligence",

                "icon":
                    "fa-brain",
            }
        )

        # -----------------------------------------------------
        # AI STRATEGY
        # -----------------------------------------------------

        timeline.append(
            {
                "time":
                    (
                        latest_action.created_at.strftime(
                            "%I:%M:%S %p"
                        )
                        if latest_action.created_at
                        else ""
                    ),

                "title":
                    "AI Strategy Generated",

                "description":
                    (
                        "Recommended action: "
                        f"{recovery_action}"
                    ),

                "status":
                    "GENERATED",

                "type":
                    "intelligence",

                "icon":
                    "fa-wand-magic-sparkles",
            }
        )

        # -----------------------------------------------------
        # GUARDRAIL
        # -----------------------------------------------------

        guardrail_passed = (
            str(guardrail).upper()
            in {
                "APPROVED",
                "PASSED",
            }
        )

        timeline.append(
            {
                "time":
                    (
                        latest_action.created_at.strftime(
                            "%I:%M:%S %p"
                        )
                        if latest_action.created_at
                        else ""
                    ),

                "title":
                    "Guardrail Validation",

                "description":
                    (
                        "All policy checks passed"
                        if guardrail_passed
                        else
                        "Recovery action blocked by policy"
                    ),

                "status":
                    str(guardrail).upper(),

                "type":
                    (
                        "completed"
                        if guardrail_passed
                        else "failed"
                    ),

                "icon":
                    "fa-shield-halved",
            }
        )

        # -----------------------------------------------------
        # RECOVERY ACTION
        # -----------------------------------------------------

        timeline.append(
            {
                "time":
                    (
                        latest_action.executed_at.strftime(
                            "%I:%M:%S %p"
                        )
                        if latest_action.executed_at
                        else
                        latest_action.created_at.strftime(
                            "%I:%M:%S %p"
                        )
                        if latest_action.created_at
                        else ""
                    ),

                "title":
                    "Recovery Action",

                "description":
                    (
                        f"{recovery_action} selected "
                        "for recovery"
                    ),

                "status":
                    str(
                        latest_action.status
                        or "PENDING"
                    ).upper(),

                "type":
                    "completed",

                "icon":
                    "fa-rotate",
            }
        )

    # ---------------------------------------------------------
    # PAYMENT RECOVERED
    # ---------------------------------------------------------

    if (
        recovery_outcome
        and str(
            recovery_outcome.outcome or ""
        ).upper() == "SUCCESS"
    ):

        timeline.append(
            {
                "time":
                    (
                        recovered_at.strftime(
                            "%I:%M:%S %p"
                        )
                        if recovered_at
                        else ""
                    ),

                "title":
                    "Payment Recovered",

                "description":
                    "Transaction successfully recovered",

                "status":
                    "SUCCESS",

                "type":
                    "recovered",

                "icon":
                    "fa-check",
            }
        )

    # =========================================================
    # WHY THIS ACTION?
    # =========================================================

    reasons = []

    if action_reason:

        reasons.append(
            str(action_reason)
        )

    if (
        customer
        and customer.historical_success_rate
        is not None
    ):

        reasons.append(
            "Customer historical success rate: "
            f"{float(customer.historical_success_rate):.1f}%"
        )

    reasons.append(
        "Current retry count is "
        f"{transaction.retry_count}, "
        "within configured limits"
    )

    if recovery_probability is not None:

        reasons.append(
            "Recovery probability is "
            f"{recovery_probability}%"
        )

    if policy:

        reasons.append(
            "Action evaluated against merchant policy: "
            f"{policy}"
        )

    # =========================================================
    # RETURN COMPLETE OBJECT
    # =========================================================

    return {

        "id":
            transaction.id,

        "transaction_id":
            transaction.transaction_id,

        "amount":
            float(
                transaction.amount or 0
            ),

        "amount_formatted":
            f"₹{float(transaction.amount or 0):,.0f}",

        "payment_method":
            transaction.payment_method,

        "failure_reason":
            failure_reason,

        "customer_name":
            customer_name,

        "customer_id":
            customer_id,

        "merchant_category":
            transaction.merchant_category,

        "payment_type":
            payment_type,

        "recovery_probability":
            recovery_probability,

        "status":
            display_status,

        "recovery_action":
            recovery_action,

        "recovery_time":
            recovery_time,

        "amount_recovered":
            amount_recovered,

        "amount_recovered_formatted":
            f"₹{amount_recovered:,.0f}",

        "customer_value":
            customer_value,

        "failure_pattern":
            failure_pattern,

        "retry_count":
            transaction.retry_count,

        "model":
            model,

        "decision_id":
            decision_id,

        "policy":
            policy,

        "guardrail":
            guardrail,

        "attempt_id":
            attempt_id,

        # PaymentAttempt does not have a Razorpay
        # payment ID column.
        "razorpay_payment_id":
            None,

        "revenue_at_risk":
            revenue_at_risk,

        "risk_score":
            risk_score,

        "created_at":
            (
                created_at.strftime(
                    "%d %b %Y, %I:%M %p"
                )
                if created_at
                else None
            ),

        "recovered_at":
            (
                recovered_at.strftime(
                    "%d %b %Y, %I:%M %p"
                )
                if recovered_at
                else None
            ),

        "recovery_time_label":
            recovery_time_label,

        "timeline":
            timeline,

        "reasons":
            reasons,
    }