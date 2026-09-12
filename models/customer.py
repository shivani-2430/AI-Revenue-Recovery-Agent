from database.db import db
from datetime import datetime


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    customer_segment = db.Column(
        db.String(50),
        nullable=False
    )

    customer_since = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    successful_payments = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    failed_payments = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    historical_success_rate = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    customer_value = db.Column(
        db.Numeric(15, 2),
        nullable=False,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    transactions = db.relationship(
        "Transaction",
        back_populates="customer",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Customer {self.customer_id}>"