from database.db import db
from datetime import datetime


class RecoveryAction(db.Model):
    __tablename__ = "recovery_actions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    transaction_id = db.Column(
        db.Integer,
        db.ForeignKey("transactions.id"),
        nullable=False,
        index=True
    )

    action_type = db.Column(
        db.String(100),
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    risk_score = db.Column(
        db.Float,
        nullable=False
    )

    recovery_probability = db.Column(
        db.Float,
        nullable=False
    )

    revenue_at_risk = db.Column(
        db.Numeric(15, 2),
        nullable=False
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="PENDING"
    )

    guardrail_status = db.Column(
        db.String(50),
        nullable=False,
        default="PENDING"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    executed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    transaction = db.relationship(
        "Transaction",
        back_populates="recovery_actions"
    )

    recovery_outcome = db.relationship(
        "RecoveryOutcome",
        back_populates="recovery_action",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<RecoveryAction "
            f"{self.action_type} "
            f"for {self.transaction_id}>"
        )