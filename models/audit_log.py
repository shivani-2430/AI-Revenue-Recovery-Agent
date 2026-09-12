from database.db import db
from datetime import datetime


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

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

    decision_id = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    decision = db.Column(
        db.String(100),
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    policy_check = db.Column(
        db.String(100),
        nullable=False
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    result = db.Column(
        db.String(100),
        nullable=False
    )

    model_version = db.Column(
        db.String(100),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    transaction = db.relationship(
        "Transaction",
        back_populates="audit_logs"
    )

    def __repr__(self):
        return (
            f"<AuditLog {self.decision_id}>"
        )