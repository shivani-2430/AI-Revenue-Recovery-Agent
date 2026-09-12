from database.db import db
from datetime import datetime


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    transaction_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False,
        index=True
    )

    amount = db.Column(
        db.Numeric(15, 2),
        nullable=False
    )

    payment_method = db.Column(
        db.String(50),
        nullable=False
    )

    merchant_category = db.Column(
        db.String(100),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False
    )

    failure_reason = db.Column(
        db.String(150),
        nullable=True
    )

    transaction_timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    subscription_status = db.Column(
        db.String(50),
        nullable=True
    )

    retry_count = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    customer = db.relationship(
        "Customer",
        back_populates="transactions"
    )

    payment_attempts = db.relationship(
        "PaymentAttempt",
        back_populates="transaction",
        cascade="all, delete-orphan"
    )

    recovery_actions = db.relationship(
        "RecoveryAction",
        back_populates="transaction",
        cascade="all, delete-orphan"
    )

    recovery_outcomes = db.relationship(
        "RecoveryOutcome",
        back_populates="transaction",
        cascade="all, delete-orphan"
    )

    audit_logs = db.relationship(
        "AuditLog",
        back_populates="transaction",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Transaction {self.transaction_id}>"
        )