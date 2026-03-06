from django.db import models
from registrations.models import UserRegistration

class PaymentRecord(models.Model):
    registration = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='payment_attempts')
    razorpay_order_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='CREATED') # CREATED, SUCCESS, FAILED
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.registration.email} - {self.razorpay_order_id} - {self.status}"
