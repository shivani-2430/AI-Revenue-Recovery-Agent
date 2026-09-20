from copy import deepcopy

from database.db import db
from models import Policy


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


def _get_or_create_policy():
    policy = (
        Policy.query
        .order_by(Policy.id.asc())
        .first()
    )

    if policy:
        return policy

    defaults = DEFAULT_POLICIES

    policy = Policy(
        minimum_recovery_probability=(
            defaults[
                "minimum_recovery_probability"
            ]
        ),
        maximum_retry_count=(
            defaults[
                "maximum_retry_count"
            ]
        ),
        retry_cooldown_minutes=(
            defaults[
                "retry_cooldown_minutes"
            ]
        ),
        maximum_auto_retry_amount=(
            defaults[
                "maximum_auto_retry_amount"
            ]
        ),
        escalation_threshold=(
            defaults[
                "escalation_threshold"
            ]
        ),
        high_value_threshold=(
            defaults[
                "high_value_threshold"
            ]
        ),
        allowed_payment_methods=deepcopy(
            defaults[
                "allowed_payment_methods"
            ]
        ),
        stop_after_success=(
            defaults["stop_rules"][
                "stop_after_success"
            ]
        ),
        stop_after_max_retries=(
            defaults["stop_rules"][
                "stop_after_max_retries"
            ]
        ),
        stop_for_low_probability=(
            defaults["stop_rules"][
                "stop_for_low_probability"
            ]
        ),
        stop_for_high_value_without_review=(
            defaults["stop_rules"][
                "stop_for_high_value_without_review"
            ]
        ),
    )

    db.session.add(policy)
    db.session.commit()

    return policy


def _serialize_policy(policy):
    return {
        "minimum_recovery_probability": float(
            policy.minimum_recovery_probability
        ),
        "maximum_retry_count": int(
            policy.maximum_retry_count
        ),
        "retry_cooldown_minutes": int(
            policy.retry_cooldown_minutes
        ),
        "maximum_auto_retry_amount": float(
            policy.maximum_auto_retry_amount
        ),
        "escalation_threshold": float(
            policy.escalation_threshold
        ),
        "high_value_threshold": float(
            policy.high_value_threshold
        ),
        "allowed_payment_methods": list(
            policy.allowed_payment_methods or []
        ),
        "stop_rules": {
            "stop_after_success": bool(
                policy.stop_after_success
            ),
            "stop_after_max_retries": bool(
                policy.stop_after_max_retries
            ),
            "stop_for_low_probability": bool(
                policy.stop_for_low_probability
            ),
            "stop_for_high_value_without_review": bool(
                policy.stop_for_high_value_without_review
            ),
        },
    }


def get_policies():
    policy = _get_or_create_policy()

    return _serialize_policy(policy)


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
    policy = _get_or_create_policy()

    if minimum_recovery_probability is not None:
        policy.minimum_recovery_probability = (
            _validate_number(
                minimum_recovery_probability,
                0,
                100,
                "Minimum recovery probability",
            )
        )

    if maximum_retry_count is not None:
        policy.maximum_retry_count = (
            _validate_integer(
                maximum_retry_count,
                0,
                10,
                "Maximum retry count",
            )
        )

    if retry_cooldown_minutes is not None:
        policy.retry_cooldown_minutes = (
            _validate_integer(
                retry_cooldown_minutes,
                0,
                1440,
                "Retry cooldown",
            )
        )

    if maximum_auto_retry_amount is not None:
        policy.maximum_auto_retry_amount = (
            _validate_number(
                maximum_auto_retry_amount,
                0,
                10000000,
                "Maximum auto retry amount",
            )
        )

    if escalation_threshold is not None:
        policy.escalation_threshold = (
            _validate_number(
                escalation_threshold,
                0,
                100,
                "Escalation threshold",
            )
        )

    if high_value_threshold is not None:
        policy.high_value_threshold = (
            _validate_number(
                high_value_threshold,
                0,
                10000000,
                "High value threshold",
            )
        )

    if allowed_payment_methods is not None:
        policy.allowed_payment_methods = (
            _normalize_payment_methods(
                allowed_payment_methods
            )
        )

    if stop_rules is not None:
        normalized_rules = _normalize_stop_rules(
            stop_rules
        )

        policy.stop_after_success = (
            normalized_rules[
                "stop_after_success"
            ]
        )

        policy.stop_after_max_retries = (
            normalized_rules[
                "stop_after_max_retries"
            ]
        )

        policy.stop_for_low_probability = (
            normalized_rules[
                "stop_for_low_probability"
            ]
        )

        policy.stop_for_high_value_without_review = (
            normalized_rules[
                "stop_for_high_value_without_review"
            ]
        )

    db.session.commit()

    return _serialize_policy(policy)


def reset_policies():
    policy = _get_or_create_policy()

    defaults = DEFAULT_POLICIES

    policy.minimum_recovery_probability = (
        defaults[
            "minimum_recovery_probability"
        ]
    )

    policy.maximum_retry_count = (
        defaults[
            "maximum_retry_count"
        ]
    )

    policy.retry_cooldown_minutes = (
        defaults[
            "retry_cooldown_minutes"
        ]
    )

    policy.maximum_auto_retry_amount = (
        defaults[
            "maximum_auto_retry_amount"
        ]
    )

    policy.escalation_threshold = (
        defaults[
            "escalation_threshold"
        ]
    )

    policy.high_value_threshold = (
        defaults[
            "high_value_threshold"
        ]
    )

    policy.allowed_payment_methods = deepcopy(
        defaults[
            "allowed_payment_methods"
        ]
    )

    policy.stop_after_success = (
        defaults["stop_rules"][
            "stop_after_success"
        ]
    )

    policy.stop_after_max_retries = (
        defaults["stop_rules"][
            "stop_after_max_retries"
        ]
    )

    policy.stop_for_low_probability = (
        defaults["stop_rules"][
            "stop_for_low_probability"
        ]
    )

    policy.stop_for_high_value_without_review = (
        defaults["stop_rules"][
            "stop_for_high_value_without_review"
        ]
    )

    db.session.commit()

    return _serialize_policy(policy)


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