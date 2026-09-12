from datetime import datetime, timedelta


def get_transaction_details(transaction_id):
    """
    Temporary frontend data provider.

    This is intentionally kept behind a service layer.
    Later this service will be replaced with PostgreSQL-backed
    transaction retrieval without changing the frontend.
    """

    transaction_id = int(transaction_id)

    payment_methods = [
        "UPI",
        "Card",
        "Net Banking",
        "Wallet",
    ]

    failure_reasons = [
        "Network Error",
        "Bank Decline",
        "Insufficient Funds",
        "Authentication Failed",
        "Gateway Timeout",
    ]

    customer_names = [
        "Rahul Kumar",
        "Ananya Sharma",
        "Vikram Patel",
        "Neha Singh",
        "Arjun Mehta",
        "Priya Kapoor",
        "Rohan Shah",
        "Sneha Kapoor",
    ]

    merchant_categories = [
        "E-commerce",
        "Travel",
        "Education",
        "Healthcare",
        "SaaS",
    ]

    recovery_actions = [
        "SMART RETRY",
        "CUSTOMER REMINDER",
        "AUTHENTICATION RETRY",
        "PAYMENT METHOD SWITCH",
        "STOP",
    ]

    policies = [
        "Network Failure Recovery Policy",
        "Bank Decline Recovery Policy",
        "Insufficient Funds Policy",
        "Authentication Recovery Policy",
        "Gateway Failure Policy",
    ]

    # ---------------------------------------------------------
    # DYNAMIC VALUES
    # ---------------------------------------------------------

    index = transaction_id - 1

    amount = (
        3500
        + ((transaction_id * 1379) % 60000)
    )

    payment_method = payment_methods[
        index % len(payment_methods)
    ]

    failure_reason = failure_reasons[
        index % len(failure_reasons)
    ]

    customer_name = customer_names[
        index % len(customer_names)
    ]

    customer_id = (
        f"CUST_{10000 + ((transaction_id * 731) % 89999):05d}"
    )

    merchant_category = merchant_categories[
        index % len(merchant_categories)
    ]

    # Recovery probability changes according to
    # transaction characteristics.

    base_probability = (
        88
        - ((transaction_id * 7) % 45)
    )

    if failure_reason == "Network Error":
        base_probability += 8

    elif failure_reason == "Insufficient Funds":
        base_probability -= 12

    elif failure_reason == "Gateway Timeout":
        base_probability -= 8

    elif failure_reason == "Authentication Failed":
        base_probability -= 3

    recovery_probability = max(
        18,
        min(96, base_probability),
    )

    retry_count = (
        transaction_id % 4
    )

    customer_value = (
        "High"
        if amount >= 30000
        else "Medium"
        if amount >= 12000
        else "Low"
    )

    if recovery_probability >= 75:
        status = "RECOVERABLE"

    elif recovery_probability >= 50:
        status = "ESCALATE"

    else:
        status = "STOP"

    # Some transactions are dynamically marked recovered
    # when their recovery probability and ID pattern indicate
    # a successful recovery.

    recovered = (
        recovery_probability >= 75
        and transaction_id % 3 == 0
    )

    if recovered:
        status = "RECOVERED"

    if recovered:
        action = "SMART RETRY"

        amount_recovered = amount

        recovery_time = (
            35 + ((transaction_id * 11) % 70)
        )

        guardrail = "PASSED"

    elif status == "RECOVERABLE":

        action = recovery_actions[
            transaction_id % 4
        ]

        amount_recovered = 0

        recovery_time = None

        guardrail = "PASSED"

    elif status == "ESCALATE":

        action = "CUSTOMER REMINDER"

        amount_recovered = 0

        recovery_time = None

        guardrail = "PASSED"

    else:

        action = "STOP"

        amount_recovered = 0

        recovery_time = None

        guardrail = "BLOCKED"

    failure_pattern = (
        "Temporary"
        if failure_reason in [
            "Network Error",
            "Gateway Timeout",
        ]
        else "Potentially Temporary"
        if failure_reason == "Bank Decline"
        else "Customer Funds"
        if failure_reason == "Insufficient Funds"
        else "Authentication"
    )

    # ---------------------------------------------------------
    # DYNAMIC TIMESTAMPS
    # ---------------------------------------------------------

    created_at = datetime.utcnow() - timedelta(
        minutes=(transaction_id % 120)
    )

    if recovered:
        recovered_at = (
            created_at
            + timedelta(seconds=recovery_time)
        )
    else:
        recovered_at = None

    # ---------------------------------------------------------
    # DYNAMIC DECISION ID
    # ---------------------------------------------------------

    decision_id = (
        f"DEC_{((transaction_id * 982451653) % 89999999):08d}"
    )

    attempt_id = (
        f"ATT_{((transaction_id * 7919) % 899999):06d}"
    )

    razorpay_payment_id = (
        f"pay_{((transaction_id * 104729) % 9999999):07d}"
    )

    # ---------------------------------------------------------
    # TIMELINE
    # ---------------------------------------------------------

    timeline = [

        {
            "time": created_at.strftime("%I:%M:%S %p"),
            "title": "Payment Initiated",
            "description":
                f"Customer started {payment_method} payment",
            "status": "COMPLETED",
            "type": "completed",
            "icon": "fa-play",
        },

        {
            "time": (
                created_at
                + timedelta(seconds=3)
            ).strftime("%I:%M:%S %p"),

            "title": "Payment Failed",

            "description":
                f"{failure_reason} · Payment attempt failed",

            "status": "FAILED",

            "type": "failed",

            "icon":
                "fa-exclamation",
        },

        {
            "time": (
                created_at
                + timedelta(seconds=5)
            ).strftime("%I:%M:%S %p"),

            "title": "ML Recovery Analysis",

            "description":
                f"Recovery probability calculated: "
                f"{recovery_probability}%",

            "status": "ANALYZED",

            "type": "intelligence",

            "icon": "fa-brain",
        },

        {
            "time": (
                created_at
                + timedelta(seconds=7)
            ).strftime("%I:%M:%S %p"),

            "title": "AI Strategy Generated",

            "description":
                f"Recommended action: {action}",

            "status": "GENERATED",

            "type": "intelligence",

            "icon":
                "fa-wand-magic-sparkles",
        },

        {
            "time": (
                created_at
                + timedelta(seconds=8)
            ).strftime("%I:%M:%S %p"),

            "title": "Guardrail Validation",

            "description":
                (
                    "All policy checks passed"
                    if guardrail == "PASSED"
                    else "Recovery action blocked by policy"
                ),

            "status": guardrail,

            "type":
                "completed"
                if guardrail == "PASSED"
                else "failed",

            "icon":
                "fa-shield-halved",
        },
    ]

    if guardrail == "PASSED":

        timeline.append(
            {
                "time": (
                    created_at
                    + timedelta(seconds=10)
                ).strftime("%I:%M:%S %p"),

                "title":
                    "Recovery Action Executed",

                "description":
                    f"{action} selected for recovery",

                "status":
                    "EXECUTED"
                    if recovered
                    else "READY",

                "type":
                    "completed",

                "icon":
                    "fa-rotate",
            }
        )

    if recovered:

        timeline.append(
            {
                "time":
                    recovered_at.strftime(
                        "%I:%M:%S %p"
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

    # ---------------------------------------------------------
    # WHY THIS ACTION?
    # ---------------------------------------------------------

    reasons = [

        (
            f"{failure_reason} pattern has "
            "historical recovery potential"
        ),

        (
            f"Customer is classified as "
            f"{customer_value.lower()} value"
        ),

        (
            f"Current retry count is "
            f"{retry_count}, within configured limits"
        ),

        (
            f"Recovery probability is "
            f"{recovery_probability}%"
        ),

        (
            "Action is evaluated against merchant policy"
        ),
    ]

    # ---------------------------------------------------------
    # RETURN COMPLETE OBJECT
    # ---------------------------------------------------------

    return {

        "id": transaction_id,

        "transaction_id":
            f"TXN_{transaction_id:07d}",

        "amount":
            amount,

        "amount_formatted":
            f"₹{amount:,.0f}",

        "payment_method":
            payment_method,

        "failure_reason":
            failure_reason,

        "customer_name":
            customer_name,

        "customer_id":
            customer_id,

        "merchant_category":
            merchant_category,

        "payment_type":
            (
                "Subscription"
                if transaction_id % 2 == 0
                else "One-time"
            ),

        "recovery_probability":
            recovery_probability,

        "status":
            status,

        "recovery_action":
            action,

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
            retry_count,

        "model":
            "Recovery-RF-v1.0",

        "decision_id":
            decision_id,

        "policy":
            policies[index % len(policies)],

        "guardrail":
            guardrail,

        "attempt_id":
            attempt_id,

        "razorpay_payment_id":
            razorpay_payment_id,

        "created_at":
            created_at.strftime(
                "%d %b %Y, %I:%M %p"
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
            (
                f"{recovery_time} seconds"
                if recovery_time
                else "Pending"
            ),

        "timeline":
            timeline,

        "reasons":
            reasons,
    }