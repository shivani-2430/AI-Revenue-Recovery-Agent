from database.db import db
from models import Customer


def get_customers(search=None, page=1, per_page=20):

    query = Customer.query

    if search:
        search_term = f"%{search.strip()}%"

        query = query.filter(
            db.or_(
                Customer.customer_id.ilike(search_term),
                Customer.customer_segment.ilike(search_term),
            )
        )

    total = query.count()

    customers = (
        query
        .order_by(Customer.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "customers": [
            {
                "id": customer.id,
                "customer_id": customer.customer_id,
                "customer_segment": customer.customer_segment,
                "customer_since": customer.customer_since.isoformat(),
                "successful_payments": customer.successful_payments,
                "failed_payments": customer.failed_payments,
                "historical_success_rate": customer.historical_success_rate,
                "customer_value": float(customer.customer_value),
                "created_at": customer.created_at.isoformat(),
                "updated_at": customer.updated_at.isoformat(),
                "transaction_count": len(customer.transactions),
            }
            for customer in customers
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
        },
    }