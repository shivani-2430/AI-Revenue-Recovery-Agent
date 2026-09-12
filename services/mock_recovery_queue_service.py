from pathlib import Path
import math

import pandas as pd


# ============================================================
# DATASET PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    BASE_DIR
    / "ml"
    / "recovery_dataset.csv"
)


# ============================================================
# SAFE HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        if pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        if value is None:
            return default

        if pd.isna(value):
            return default

        return int(float(value))

    except (TypeError, ValueError):
        return default


def _safe_string(value, default=""):
    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass

    return str(value)


# ============================================================
# CURRENCY FORMAT
# ============================================================

def _format_currency(amount):
    amount = _safe_float(amount)

    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f}Cr"

    if amount >= 100_000:
        return f"₹{amount / 100_000:.2f}L"

    if amount >= 1_000:
        return f"₹{amount / 1_000:.1f}K"

    return f"₹{amount:,.0f}"


# ============================================================
# CUSTOMER LABEL
# ============================================================

def _customer_label(customer_id):
    value = _safe_string(
        customer_id,
        "CUSTOMER",
    )

    return value[-8:]


# ============================================================
# NORMALIZE PROBABILITY
# ============================================================

def _normalize_probability(value):
    probability = _safe_float(value)

    # Dataset may contain:
    # 0.87 -> 87
    # 0.62 -> 62
    if 0 <= probability <= 1:
        probability *= 100

    return max(
        0,
        min(
            100,
            probability,
        ),
    )


# ============================================================
# PRIORITY
# ============================================================

def _priority(
    probability,
    amount,
    retry_count,
):
    probability = _normalize_probability(
        probability
    )

    amount = max(
        0,
        _safe_float(amount),
    )

    retry_count = max(
        0,
        _safe_int(retry_count),
    )

    score = (
        probability * 0.60
        + min(
            amount / 100_000,
            1,
        ) * 25
        + max(
            0,
            3 - retry_count,
        ) * 5
    )

    if score >= 70:
        return "HIGH"

    if score >= 45:
        return "MEDIUM"

    return "LOW"


# ============================================================
# RECOMMENDED ACTION
# ============================================================

def _recommended_action(
    row,
    probability,
):
    failure_reason = _safe_string(
        row.get("failure_reason")
    ).lower()

    retry_count = _safe_int(
        row.get("retry_count")
    )

    probability = _normalize_probability(
        probability
    )

    if probability < 35:
        return "STOP"

    if (
        "network" in failure_reason
        or "timeout" in failure_reason
    ):
        return "SMART RETRY"

    if "authentication" in failure_reason:
        return "AUTHENTICATION RETRY"

    if "bank" in failure_reason:
        return "PAYMENT RETRY"

    if "insufficient" in failure_reason:
        return "CUSTOMER REMINDER"

    if retry_count >= 3:
        return "CUSTOMER REMINDER"

    return "SMART RETRY"


# ============================================================
# STATUS
# ============================================================

def _status(probability):
    probability = _normalize_probability(
        probability
    )

    if probability >= 70:
        return "READY"

    if probability >= 45:
        return "PENDING"

    return "STOPPED"


# ============================================================
# GUARDRAIL
# ============================================================

def _guardrail(
    probability,
    retry_count,
):
    probability = _normalize_probability(
        probability
    )

    retry_count = _safe_int(
        retry_count
    )

    if probability < 35:
        return "BLOCKED"

    if retry_count >= 3:
        return "REVIEW"

    return "PASSED"


# ============================================================
# BUILD ONE OPPORTUNITY
# ============================================================

def _build_opportunity(row):

    probability = _normalize_probability(
        row.get("recovery_probability")
    )

    amount = _safe_float(
        row.get("amount")
    )

    retry_count = _safe_int(
        row.get("retry_count")
    )

    revenue_at_risk = amount

    expected_recovery = (
        amount
        * probability
        / 100
    )

    priority = _priority(
        probability,
        amount,
        retry_count,
    )

    recommended_action = (
        _recommended_action(
            row,
            probability,
        )
    )

    guardrail = _guardrail(
        probability,
        retry_count,
    )

    status = _status(
        probability
    )

    return {
        "transaction_id": _safe_string(
            row.get("transaction_id"),
            "UNKNOWN",
        ),

        "customer_id": _safe_string(
            row.get("customer_id"),
            "UNKNOWN",
        ),

        "customer_label": _customer_label(
            row.get("customer_id")
        ),

        "customer_segment": _safe_string(
            row.get(
                "customer_segment"
            ),
            "STANDARD",
        ),

        "amount": round(
            amount,
            2,
        ),

        "amount_label": _format_currency(
            amount
        ),

        "failure_reason": _safe_string(
            row.get("failure_reason"),
            "Unknown",
        ),

        "payment_method": _safe_string(
            row.get("payment_method"),
            "Unknown",
        ),

        "recovery_probability": round(
            probability,
            1,
        ),

        "revenue_at_risk": round(
            revenue_at_risk,
            2,
        ),

        "revenue_at_risk_label":
            _format_currency(
                revenue_at_risk
            ),

        "expected_recovery": round(
            expected_recovery,
            2,
        ),

        "expected_recovery_label":
            _format_currency(
                expected_recovery
            ),

        "priority": priority,

        "recommended_action":
            recommended_action,

        "guardrail": guardrail,

        "status": status,

        "retry_count": retry_count,

        "high_value_customer": bool(
            row.get(
                "high_value_customer",
                False,
            )
        ),

        "subscription_status":
            _safe_string(
                row.get(
                    "subscription_status"
                ),
                "UNKNOWN",
            ),

        "timestamp": _safe_string(
            row.get(
                "transaction_timestamp"
            )
        ),
    }


# ============================================================
# MAIN RECOVERY QUEUE
# ============================================================

def get_recovery_queue(
    search=None,
    priority=None,
    status=None,
    failure_reason=None,
    payment_method=None,
    page=1,
    per_page=10,
    sort="opportunity",
):

    # --------------------------------------------------------
    # VERIFY DATASET
    # --------------------------------------------------------

    if not DATASET_PATH.exists():

        raise FileNotFoundError(
            "Recovery dataset was not found.\n"
            f"Expected location:\n{DATASET_PATH}"
        )

    # --------------------------------------------------------
    # LOAD DATASET
    # --------------------------------------------------------

    dataframe = pd.read_csv(
        DATASET_PATH
    )

    if dataframe.empty:

        raise ValueError(
            "Recovery dataset exists, "
            "but it contains no records."
        )

    # --------------------------------------------------------
    # VERIFY COLUMNS
    # --------------------------------------------------------

    required_columns = {
        "transaction_id",
        "customer_id",
        "amount",
        "payment_method",
        "failure_reason",
        "status",
        "recovery_probability",
    }

    missing_columns = (
        required_columns
        - set(dataframe.columns)
    )

    if missing_columns:

        raise ValueError(
            "Recovery dataset is missing "
            "required columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    # --------------------------------------------------------
    # FAILED PAYMENTS
    # --------------------------------------------------------

    failed = dataframe[
        dataframe["status"]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("FAILED")
    ].copy()

    # --------------------------------------------------------
    # NORMALIZE RECOVERY PROBABILITY
    # --------------------------------------------------------

    failed[
        "recovery_probability"
    ] = pd.to_numeric(
        failed[
            "recovery_probability"
        ],
        errors="coerce",
    ).fillna(0)

    if not failed.empty:

        maximum_probability = (
            failed[
                "recovery_probability"
            ].max()
        )

        if maximum_probability <= 1:

            failed[
                "recovery_probability"
            ] = (
                failed[
                    "recovery_probability"
                ]
                * 100
            )

    failed[
        "recovery_probability"
    ] = (
        failed[
            "recovery_probability"
        ]
        .clip(
            lower=0,
            upper=100,
        )
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        search_value = (
            str(search)
            .strip()
            .lower()
        )

        transaction_match = (
            failed[
                "transaction_id"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                search_value,
                na=False,
            )
        )

        customer_match = (
            failed[
                "customer_id"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                search_value,
                na=False,
            )
        )

        failure_match = (
            failed[
                "failure_reason"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                search_value,
                na=False,
            )
        )

        payment_match = (
            failed[
                "payment_method"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                search_value,
                na=False,
            )
        )

        failed = failed[
            transaction_match
            | customer_match
            | failure_match
            | payment_match
        ]

    # --------------------------------------------------------
    # CREATE OPPORTUNITIES
    # --------------------------------------------------------

    opportunities = [
        _build_opportunity(row)
        for _, row in failed.iterrows()
    ]

    # --------------------------------------------------------
    # PRIORITY FILTER
    # --------------------------------------------------------

    if priority:

        priority_value = (
            str(priority)
            .strip()
            .upper()
        )

        opportunities = [
            item
            for item in opportunities
            if item["priority"]
            == priority_value
        ]

    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    if status:

        status_value = (
            str(status)
            .strip()
            .upper()
        )

        opportunities = [
            item
            for item in opportunities
            if item["status"]
            == status_value
        ]

    # --------------------------------------------------------
    # FAILURE FILTER
    # --------------------------------------------------------

    if failure_reason:

        failure_value = (
            str(failure_reason)
            .strip()
            .lower()
        )

        opportunities = [
            item
            for item in opportunities
            if item[
                "failure_reason"
            ].lower()
            == failure_value
        ]

    # --------------------------------------------------------
    # PAYMENT METHOD FILTER
    # --------------------------------------------------------

    if payment_method:

        payment_value = (
            str(payment_method)
            .strip()
            .lower()
        )

        opportunities = [
            item
            for item in opportunities
            if item[
                "payment_method"
            ].lower()
            == payment_value
        ]

    # ========================================================
    # SORT
    # ========================================================

    sort_value = (
        str(sort or "opportunity")
        .strip()
        .lower()
    )

    if sort_value == "probability":

        opportunities.sort(
            key=lambda item:
                item[
                    "recovery_probability"
                ],
            reverse=True,
        )

    elif sort_value == "amount":

        opportunities.sort(
            key=lambda item:
                item[
                    "revenue_at_risk"
                ],
            reverse=True,
        )

    elif sort_value == "expected_recovery":

        opportunities.sort(
            key=lambda item:
                item[
                    "expected_recovery"
                ],
            reverse=True,
        )

    else:

        opportunities.sort(
            key=lambda item: (
                {
                    "HIGH": 3,
                    "MEDIUM": 2,
                    "LOW": 1,
                }.get(
                    item["priority"],
                    0,
                ),

                item[
                    "expected_recovery"
                ],

                item[
                    "recovery_probability"
                ],

                item["amount"],
            ),
            reverse=True,
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    total_opportunities = len(
        opportunities
    )

    revenue_at_risk = sum(
        item[
            "revenue_at_risk"
        ]
        for item in opportunities
    )

    expected_recovery = sum(
        item[
            "expected_recovery"
        ]
        for item in opportunities
    )

    high_priority = sum(
        1
        for item in opportunities
        if item["priority"]
        == "HIGH"
    )

    medium_priority = sum(
        1
        for item in opportunities
        if item["priority"]
        == "MEDIUM"
    )

    low_priority = sum(
        1
        for item in opportunities
        if item["priority"]
        == "LOW"
    )

    recovery_potential = (
        (
            expected_recovery
            / revenue_at_risk
        )
        * 100
        if revenue_at_risk > 0
        else 0
    )

    # ========================================================
    # FAILURE DRIVERS
    # ========================================================

    driver_frame = failed.copy()

    drivers = []

    if not driver_frame.empty:

        driver_frame[
            "amount"
        ] = pd.to_numeric(
            driver_frame["amount"],
            errors="coerce",
        ).fillna(0)

        driver_groups = (
            driver_frame
            .groupby(
                "failure_reason",
                dropna=False,
            )
            .agg(
                volume=(
                    "failure_reason",
                    "size",
                ),
                revenue_at_risk=(
                    "amount",
                    "sum",
                ),
            )
            .reset_index()
            .sort_values(
                "revenue_at_risk",
                ascending=False,
            )
        )

        total_driver_volume = max(
            int(
                driver_groups[
                    "volume"
                ].sum()
            ),
            1,
        )

        for _, row in driver_groups.head(
            5
        ).iterrows():

            name = _safe_string(
                row[
                    "failure_reason"
                ],
                "Unknown",
            )

            volume = _safe_int(
                row["volume"]
            )

            revenue = _safe_float(
                row[
                    "revenue_at_risk"
                ]
            )

            drivers.append(
                {
                    "name": name,

                    "volume": volume,

                    "share": round(
                        (
                            volume
                            / total_driver_volume
                        )
                        * 100,
                        1,
                    ),

                    "revenue_at_risk":
                        round(
                            revenue,
                            2,
                        ),

                    "revenue_at_risk_label":
                        _format_currency(
                            revenue
                        ),
                }
            )

    # ========================================================
    # PAYMENT METHODS
    # ========================================================

    payment_methods = []

    if not failed.empty:

        payment_groups = (
            failed
            .groupby(
                "payment_method",
                dropna=False,
            )
            .size()
            .reset_index(
                name="volume"
            )
            .sort_values(
                "volume",
                ascending=False,
            )
        )

        total_payment_volume = max(
            int(
                payment_groups[
                    "volume"
                ].sum()
            ),
            1,
        )

        for _, row in payment_groups.iterrows():

            name = _safe_string(
                row[
                    "payment_method"
                ],
                "Unknown",
            )

            volume = _safe_int(
                row["volume"]
            )

            payment_methods.append(
                {
                    "name": name,

                    "volume": volume,

                    "share": round(
                        (
                            volume
                            / total_payment_volume
                        )
                        * 100,
                        1,
                    ),
                }
            )

    # ========================================================
    # PAGINATION
    # ========================================================

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
        math.ceil(
            total_opportunities
            / per_page
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

    paginated = opportunities[
        start:end
    ]

    # ========================================================
    # STRATEGY
    # ========================================================

    if total_opportunities == 0:

        strategy_priority = "LOW"

        strategy_focus = (
            "No recovery opportunities "
            "currently match the selected filters."
        )

    elif high_priority > 0:

        strategy_priority = "HIGH"

        strategy_focus = (
            "Prioritize high-value opportunities "
            "with strong recovery probability."
        )

    elif medium_priority > 0:

        strategy_priority = "MEDIUM"

        strategy_focus = (
            "Review medium-confidence opportunities "
            "and apply recovery actions only within "
            "configured guardrails."
        )

    else:

        strategy_priority = "LOW"

        strategy_focus = (
            "Review lower-confidence opportunities "
            "before taking recovery action."
        )

    # ========================================================
    # FINAL DATA CONTRACT
    # ========================================================

    return {

        "summary": {

            "eligible_opportunities":
                total_opportunities,

            "eligible_opportunities_label":
                f"{total_opportunities:,}",

            "revenue_at_risk":
                round(
                    revenue_at_risk,
                    2,
                ),

            "revenue_at_risk_label":
                _format_currency(
                    revenue_at_risk
                ),

            "expected_recovery":
                round(
                    expected_recovery,
                    2,
                ),

            "expected_recovery_label":
                _format_currency(
                    expected_recovery
                ),

            "high_priority":
                high_priority,

            "high_priority_label":
                f"{high_priority:,}",

            "medium_priority":
                medium_priority,

            "medium_priority_label":
                f"{medium_priority:,}",

            "low_priority":
                low_priority,

            "low_priority_label":
                f"{low_priority:,}",

            "recovery_potential":
                round(
                    recovery_potential,
                    1,
                ),
        },

        "opportunities":
            paginated,

        "drivers":
            drivers,

        "payment_methods":
            payment_methods,

        "pagination": {

            "page":
                page,

            "per_page":
                per_page,

            "total":
                total_opportunities,

            "total_pages":
                total_pages,
        },

        "ai_strategy": {

            "priority":
                strategy_priority,

            "focus":
                strategy_focus,

            "expected_recovery_label":
                _format_currency(
                    expected_recovery
                ),

            "opportunity_count":
                high_priority,
        },
    }