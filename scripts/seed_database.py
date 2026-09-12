import csv
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import app
from database.db import db
from models import Customer, Transaction


CSV_PATH = "ml/recovery_dataset.csv"


with app.app_context():

    customers_by_id = {}
    transaction_rows = []

    with open(
        CSV_PATH,
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            customer_id = row["customer_id"]

            # Create each customer only once
            if customer_id not in customers_by_id:

                transaction_time = datetime.fromisoformat(
                    row["transaction_timestamp"]
                )

                customer_age_days = int(
                    row["customer_age_days"]
                )

                customers_by_id[customer_id] = Customer(
                    customer_id=customer_id,
                    customer_segment=row["customer_segment"],
                    customer_since=(
                        transaction_time
                        - timedelta(days=customer_age_days)
                    ),
                    successful_payments=int(
                        row["successful_payments"]
                    ),
                    failed_payments=int(
                        row["failed_payments"]
                    ),
                    historical_success_rate=float(
                        row["historical_success_rate"]
                    ),
                    customer_value=Decimal(
                        row["customer_value"]
                    )
                )

            transaction_rows.append(
                {
                    "transaction_id": row["transaction_id"],
                    "customer_id": customer_id,
                    "amount": Decimal(row["amount"]),
                    "payment_method": row["payment_method"],
                    "merchant_category": row["merchant_category"],
                    "status": row["status"],
                    "failure_reason": (
                        row["failure_reason"]
                        if row["failure_reason"]
                        else None
                    ),
                    "transaction_timestamp": datetime.fromisoformat(
                        row["transaction_timestamp"]
                    ),
                    "subscription_status": (
                        row["subscription_status"]
                        if row["subscription_status"]
                        else None
                    ),
                    "retry_count": int(row["retry_count"])
                }
            )

    # Insert customers first because transactions
    # reference customers.id
    db.session.add_all(customers_by_id.values())
    db.session.flush()

    customer_db_ids = {
        customer.customer_id: customer.id
        for customer in customers_by_id.values()
    }

    transactions = []

    for row in transaction_rows:

        transactions.append(
            Transaction(
                transaction_id=row["transaction_id"],
                customer_id=customer_db_ids[row["customer_id"]],
                amount=row["amount"],
                payment_method=row["payment_method"],
                merchant_category=row["merchant_category"],
                status=row["status"],
                failure_reason=row["failure_reason"],
                transaction_timestamp=row["transaction_timestamp"],
                subscription_status=row["subscription_status"],
                retry_count=row["retry_count"]
            )
        )

    db.session.add_all(transactions)
    db.session.commit()

    print("========================================")
    print("RecoverAI database seeded successfully")
    print("========================================")
    print(f"Customers inserted: {len(customers_by_id)}")
    print(f"Transactions inserted: {len(transactions)}")
    print("========================================")