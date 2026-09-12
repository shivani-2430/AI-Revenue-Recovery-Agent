from database.db import db
from datetime import datetime


class RecoveryOutcome(db.Model):
    __tablename__ = "recovery_outcomes"

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

    recovery_action_id = db.Column(
        db.Integer,
        db.ForeignKey("recovery_actions.id"),
        nullable=False,
        unique=True
    )

    outcome = db.Column(
        db.String(50),
        nullable=False
    )

    amount_recovered = db.Column(
        db.Numeric(15, 2),
        nullable=False,
        default=0
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    transaction = db.relationship(
        "Transaction",
        back_populates="recovery_outcomes"
    )

    recovery_action = db.relationship(
        "RecoveryAction",
        back_populates="recovery_outcome"
    )

    def __repr__(self):
        return (
            f"<RecoveryOutcome "
            f"{self.transaction_id}: "
            f"{self.outcome}>"
        )