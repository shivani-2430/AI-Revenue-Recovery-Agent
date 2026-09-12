import os
import time
import razorpay
from dotenv import load_dotenv

load_dotenv()


def _get_client():
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        return None

    return razorpay.Client(
        auth=(key_id, key_secret)
    )


def is_configured():
    return bool(
        os.getenv("RAZORPAY_KEY_ID")
        and os.getenv("RAZORPAY_KEY_SECRET")
    )


def fetch_payment(payment_id):
    client = _get_client()

    if not client:
        return {
            "success": False,
            "configured": False,
            "error": "Razorpay credentials are not configured."
        }

    try:
        payment = client.payment.fetch(
            payment_id
        )

        return {
            "success": True,
            "configured": True,
            "payment": payment
        }

    except Exception as error:
        return {
            "success": False,
            "configured": True,
            "error": str(error)
        }


def capture_payment(payment_id, amount):
    client = _get_client()

    if not client:
        return {
            "success": False,
            "configured": False,
            "error": "Razorpay credentials are not configured."
        }

    amount_paise = int(
        round(float(amount) * 100)
    )

    try:
        payment = client.payment.capture(
            payment_id,
            amount_paise
        )

        return {
            "success": True,
            "configured": True,
            "payment": payment
        }

    except Exception as error:
        return {
            "success": False,
            "configured": True,
            "error": str(error)
        }


def create_payment_link(
    amount,
    reference_id,
    customer_name=None,
    customer_email=None,
    customer_contact=None,
    description=None,
    notes=None
):
    client = _get_client()

    if not client:
        return {
            "success": False,
            "configured": False,
            "error": "Razorpay credentials are not configured."
        }

    amount_paise = int(
        round(float(amount) * 100)
    )

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "reference_id": str(reference_id)[:40],
        "description": (
            description
            or "RecoverAI payment recovery"
        ),
        "expire_by": int(
            time.time() + 86400
        ),
        "reminder_enable": True
    }

    customer = {}

    if customer_name:
        customer["name"] = customer_name

    if customer_email:
        customer["email"] = customer_email

    if customer_contact:
        customer["contact"] = customer_contact

    if customer:
        payload["customer"] = customer

    if notes:
        payload["notes"] = notes

    try:
        payment_link = client.payment_link.create(
            payload
        )

        return {
            "success": True,
            "configured": True,
            "payment_link": payment_link
        }

    except Exception as error:
        return {
            "success": False,
            "configured": True,
            "error": str(error)
        }
