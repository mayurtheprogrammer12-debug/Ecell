import razorpay
from django.conf import settings

def get_razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_SECRET_KEY:
        raise ValueError("Razorpay credentials not set.")
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

def create_razorpay_order(amount, currency="INR"):
    client = get_razorpay_client()
    data = {
        "amount": int(amount * 100), # Amount in paise
        "currency": currency,
        "payment_capture": 1
    }
    return client.order.create(data=data)

def verify_razorpay_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    client = get_razorpay_client()
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }
    try:
        client.utility.verify_payment_signature(params_dict)
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
