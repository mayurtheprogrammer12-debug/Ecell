from django.db import models
from registrations.models import UserRegistration

class PaymentRecord(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('free', 'Free')
    )
    registration = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='payment_attempts')
    reference_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    screenshot = models.ImageField(upload_to='payment_screenshots/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.registration.email} - {self.reference_id} - {self.payment_status}"
