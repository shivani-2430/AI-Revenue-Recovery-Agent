from database.db import db
from datetime import datetime


class PaymentAttempt(db.Model):
    __tablename__ = "payment_attempts"

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

    attempt_number = db.Column(
        db.Integer,
        nullable=False
    )

    attempted_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    status = db.Column(
        db.String(30),
        nullable=False
    )

    failure_reason = db.Column(
        db.String(150),
        nullable=True
    )

    response_code = db.Column(
        db.String(100),
        nullable=True
    )

    transaction = db.relationship(
        "Transaction",
        back_populates="payment_attempts"
    )

    def __repr__(self):
        return (
            f"<PaymentAttempt "
            f"{self.transaction_id} "
            f"#{self.attempt_number}>"
        )