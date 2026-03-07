from django.db import models
from referrals.models import ReferralCode

class UserRegistration(models.Model):
    REGISTRATION_TYPES = (
        ('PARTICIPANT', 'Participant'),
        ('EXHIBITOR', 'Exhibitor'),
        ('VISITOR', 'Visitor'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('FREE', 'Free')
    )

    EXHIBITOR_CATEGORIES = (
        ('EXHIBITION', 'Exhibition Partner'),
        ('WORKSHOP', 'Workshop Partner'),
        ('MERCHANDISED', 'Merchandised Partner'),
        ('MEDIA', 'Media Partner'),
    )

    # Common Fields
    name = models.CharField(max_length=255, help_text="Full legal name as per ID")
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True, null=True, help_text="Gender identity")
    age = models.PositiveIntegerField(blank=True, null=True, help_text="Chronological age")
    phone = models.CharField(max_length=20, help_text="Active contact sequence")
    email = models.EmailField(unique=True, help_text="Official communication node")
    city = models.CharField(max_length=100, blank=True, null=True, help_text="City of residence")
    college = models.CharField(max_length=255, blank=True, null=True, help_text="Institutional affiliation / Organisation")
    registration_type = models.CharField(max_length=20, choices=REGISTRATION_TYPES)
    exhibitor_category = models.CharField(max_length=50, choices=EXHIBITOR_CATEGORIES, blank=True, null=True, help_text="Category of exhibition partnership")

    # Exhibitor Specific
    org_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Organization/Startup Name", help_text="Venture or entity designation")
    description = models.TextField(blank=True, null=True, verbose_name="Product/Startup Description", help_text="Brief technical or business core")
    website = models.URLField(blank=True, null=True, verbose_name="Website/Social Media Link", help_text="Digital archive or portfolio")

    # Payment & Pricing
    referral_code_used = models.ForeignKey(ReferralCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='registrations')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')

    # UPI Payment
    reference_id = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Payment Reference ID")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.registration_type}"

    @property
    def is_pccoe(self):
        return self.email.endswith('@pccoepune.org')
