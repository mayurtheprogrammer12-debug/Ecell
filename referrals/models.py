from django.db import models

class ReferralCode(models.Model):
    referral_code = models.CharField(max_length=50, unique=True)
    ambassador_name = models.CharField(max_length=255)
    ambassador_email = models.EmailField()
    discount_percentage = models.PositiveIntegerField(help_text="Discount percentage (0-100)")
    max_usage = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of times this code can be used")
    current_usage = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.referral_code

    @property
    def is_valid(self):
        if self.max_usage is not None and self.current_usage >= self.max_usage:
            return False
        return True
