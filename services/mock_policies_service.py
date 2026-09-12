from copy import deepcopy
from threading import Lock


DEFAULT_POLICIES = {
    "minimum_recovery_probability": 40,
    "maximum_retry_count": 3,
    "retry_cooldown_minutes": 30,
    "maximum_auto_retry_amount": 50000,
    "escalation_threshold": 70,
    "high_value_threshold": 100000,
    "allowed_payment_methods": [
        "UPI",
        "CARD",
        "NETBANKING",
        "WALLET",
    ],
    "stop_rules": {
        "stop_after_success": True,
        "stop_after_max_retries": True,
        "stop_for_low_probability": True,
        "stop_for_high_value_without_review": True,
    },
}


_policy_state = deepcopy(DEFAULT_POLICIES)
_policy_lock = Lock()


def _validate_number(
    value,
    minimum,
    maximum,
    name,
):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{name} must be a number."
        )

    if value < minimum or value > maximum:
        raise ValueError(
            f"{name} must be between "
            f"{minimum} and {maximum}."
        )

    return value


def _validate_integer(
    value,
    minimum,
    maximum,
    name,
):
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{name} must be an integer."
        )

    if value < minimum or value > maximum:
        raise ValueError(
            f"{name} must be between "
            f"{minimum} and {maximum}."
        )

    return value


def _normalize_payment_methods(methods):
    if not isinstance(methods, list):
        raise ValueError(
            "Allowed payment methods must be a list."
        )

    normalized = []

    for method in methods:
        value = str(method).strip().upper()

        if value and value not in normalized:
            normalized.append(value)

    if not normalized:
        raise ValueError(
            "At least one payment method must be allowed."
        )

    return normalized


def _normalize_stop_rules(stop_rules):
    if not isinstance(stop_rules, dict):
        raise ValueError(
            "Stop rules must be an object."
        )

    normalized = deepcopy(
        DEFAULT_POLICIES["stop_rules"]
    )

    for key in normalized:
        if key in stop_rules:
            normalized[key] = bool(
                stop_rules[key]
            )

    return normalized


def get_policies():
    with _policy_lock:
        return deepcopy(_policy_state)


def update_policies(
    minimum_recovery_probability=None,
    maximum_retry_count=None,
    retry_cooldown_minutes=None,
    maximum_auto_retry_amount=None,
    escalation_threshold=None,
    high_value_threshold=None,
    allowed_payment_methods=None,
    stop_rules=None,
):
    with _policy_lock:
        if minimum_recovery_probability is not None:
            _policy_state[
                "minimum_recovery_probability"
            ] = _validate_number(
                minimum_recovery_probability,
                0,
                100,
                "Minimum recovery probability",
            )

        if maximum_retry_count is not None:
            _policy_state[
                "maximum_retry_count"
            ] = _validate_integer(
                maximum_retry_count,
                0,
                10,
                "Maximum retry count",
            )

        if retry_cooldown_minutes is not None:
            _policy_state[
                "retry_cooldown_minutes"
            ] = _validate_integer(
                retry_cooldown_minutes,
                0,
                1440,
                "Retry cooldown",
            )

        if maximum_auto_retry_amount is not None:
            _policy_state[
                "maximum_auto_retry_amount"
            ] = _validate_number(
                maximum_auto_retry_amount,
                0,
                10000000,
                "Maximum auto retry amount",
            )

        if escalation_threshold is not None:
            _policy_state[
                "escalation_threshold"
            ] = _validate_number(
                escalation_threshold,
                0,
                100,
                "Escalation threshold",
            )

        if high_value_threshold is not None:
            _policy_state[
                "high_value_threshold"
            ] = _validate_number(
                high_value_threshold,
                0,
                10000000,
                "High value threshold",
            )

        if allowed_payment_methods is not None:
            _policy_state[
                "allowed_payment_methods"
            ] = _normalize_payment_methods(
                allowed_payment_methods
            )

        if stop_rules is not None:
            _policy_state[
                "stop_rules"
            ] = _normalize_stop_rules(
                stop_rules
            )

        return deepcopy(_policy_state)


def reset_policies():
    global _policy_state

    with _policy_lock:
        _policy_state = deepcopy(
            DEFAULT_POLICIES
        )

        return deepcopy(_policy_state)


def evaluate_guardrails(
    recovery_probability,
    retry_count,
    amount,
    payment_method,
):
    policies = get_policies()

    probability = _validate_number(
        recovery_probability,
        0,
        100,
        "Recovery probability",
    )

    retry_count = _validate_integer(
        retry_count,
        0,
        100,
        "Retry count",
    )

    amount = _validate_number(
        amount,
        0,
        1000000000,
        "Amount",
    )

    payment_method = (
        str(payment_method or "")
        .strip()
        .upper()
    )

    reasons = []
    status = "APPROVED"

    stop_rules = policies["stop_rules"]

    if (
        stop_rules["stop_for_low_probability"]
        and probability
        < policies[
            "minimum_recovery_probability"
        ]
    ):
        reasons.append(
            "Recovery probability is below policy threshold."
        )
        status = "BLOCKED"

    if (
        stop_rules["stop_after_max_retries"]
        and retry_count
        >= policies[
            "maximum_retry_count"
        ]
    ):
        reasons.append(
            "Maximum retry count has been reached."
        )
        status = "BLOCKED"

    if (
        payment_method
        not in policies[
            "allowed_payment_methods"
        ]
    ):
        reasons.append(
            "Payment method is not allowed by policy."
        )
        status = "BLOCKED"

    if (
        amount
        > policies[
            "maximum_auto_retry_amount"
        ]
        and probability
        >= policies[
            "minimum_recovery_probability"
        ]
    ):
        reasons.append(
            "Transaction exceeds automatic retry amount limit."
        )
        status = "ESCALATED"

    if (
        stop_rules[
            "stop_for_high_value_without_review"
        ]
        and amount
        >= policies[
            "high_value_threshold"
        ]
    ):
        reasons.append(
            "High-value transaction requires review."
        )
        status = "ESCALATED"

    if (
        probability
        >= policies[
            "escalation_threshold"
        ]
        and status == "APPROVED"
    ):
        reasons.append(
            "High recovery probability qualifies for priority recovery."
        )

    if not reasons:
        reasons.append(
            "All configured recovery guardrails passed."
        )

    return {
        "status": status,
        "passed": status == "APPROVED",
        "reasons": reasons,
        "policy": policies,
    }