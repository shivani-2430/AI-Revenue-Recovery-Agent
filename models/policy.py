from datetime import datetime

from database.db import db


class Policy(db.Model):
    __tablename__ = "policies"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    minimum_recovery_probability = db.Column(
        db.Float,
        nullable=False,
        default=40,
    )

    maximum_retry_count = db.Column(
        db.Integer,
        nullable=False,
        default=3,
    )

    retry_cooldown_minutes = db.Column(
        db.Integer,
        nullable=False,
        default=30,
    )

    maximum_auto_retry_amount = db.Column(
        db.Numeric(15, 2),
        nullable=False,
        default=50000,
    )

    escalation_threshold = db.Column(
        db.Float,
        nullable=False,
        default=70,
    )

    high_value_threshold = db.Column(
        db.Numeric(15, 2),
        nullable=False,
        default=100000,
    )

    allowed_payment_methods = db.Column(
        db.JSON,
        nullable=False,
        default=lambda: [
            "UPI",
            "CARD",
            "NETBANKING",
            "WALLET",
        ],
    )

    stop_after_success = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    stop_after_max_retries = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    stop_for_low_probability = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    stop_for_high_value_without_review = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )