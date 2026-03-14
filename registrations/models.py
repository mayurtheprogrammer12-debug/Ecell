from django.db import models
import uuid

class EventSettings(models.Model):
    event_name = models.CharField(max_length=255, default="Ennovate'X-26")
    is_registration_open = models.BooleanField(default=True)
    round1_name = models.CharField(max_length=100, default="Round 1")
    round2_name = models.CharField(max_length=100, default="Round 2")
    contact_email = models.EmailField(default="nexus@ecellpccoe.com")

    def __str__(self):
        return self.event_name

    class Meta:
        verbose_name = "Event Settings"
        verbose_name_plural = "Event Settings"
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
    def is_free_eligible(self):
        # Check specific emails first
        if FreeEntryWhitelist.objects.filter(whitelist_type='EMAIL', value=self.email).exists():
            return True
        
        # Check domains
        domain = self.email.split('@')[-1]
        if FreeEntryWhitelist.objects.filter(whitelist_type='DOMAIN', value=domain).exists():
            return True
            
        # Default legacy check
        return self.email.endswith('@pccoepune.org')

    @property
    def is_pccoe(self):
        return self.is_free_eligible

    # Auth & Dashboard Link
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='registration', null=True, blank=True)
    
    # Event Progress
    round1_completed = models.BooleanField(default=False)
    round1_submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Round 1 Submission Data
    idea_title = models.CharField(max_length=255, blank=True, null=True)
    idea_description = models.TextField(blank=True, null=True)
    idea_domain = models.CharField(max_length=100, blank=True, null=True)
    idea_agreement = models.BooleanField(default=False)

    selected_for_round2 = models.BooleanField(default=False)
    round2_unlocked = models.BooleanField(default=False)
    round2_completed = models.BooleanField(default=False)
    
    selected_for_round3 = models.BooleanField(default=False)
    round3_unlocked = models.BooleanField(default=False)
    round3_completed = models.BooleanField(default=False)

    # Email Tracking
    registration_email_sent = models.BooleanField(default=False)
    round2_email_sent = models.BooleanField(default=False)

    @property
    def in_team(self):
        return hasattr(self, 'team_membership') or self.created_teams.exists()
    
    def get_team(self):
        if hasattr(self, 'team_membership'):
            return self.team_membership.team
        return self.created_teams.first()


class FreeEntryWhitelist(models.Model):
    WHITELIST_TYPES = (
        ('DOMAIN', 'Email Domain (e.g., gmail.com)'),
        ('EMAIL', 'Specific Email Address'),
    )
    
    value = models.CharField(max_length=255, help_text="The domain or email to whitelist", unique=True)
    whitelist_type = models.CharField(max_length=10, choices=WHITELIST_TYPES, default='DOMAIN')
    description = models.CharField(max_length=255, blank=True, null=True, help_text="Reason or note for this whitelist entry")

    def __str__(self):
        return f"{self.whitelist_type}: {self.value}"

    class Meta:
        verbose_name_plural = "Free Entry Whitelist"
import uuid

class AttendanceSession(models.Model):
    name = models.CharField(max_length=255, help_text="e.g. Event Check-in, Round 1 Attendance")
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Closed'})"

    @property
    def qr_data(self):
        # This will be used to generate the QR code URL
        return f"/attendance/checkin/{self.session_id}/"

class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
    )
    
    participant = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='attendance_records')
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ABSENT')

    class Meta:
        unique_together = ('participant', 'session')

    def __str__(self):
        return f"{self.participant.name} - {self.session.name}: {self.status}"

class Team(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
    )

    team_name = models.CharField(max_length=255)
    team_id = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    creator = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='created_teams')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    selected_for_round3 = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.team_id:
            from django.db.models import Max
            max_id = Team.objects.aggregate(Max('id'))['id__max'] or 0
            new_id = max_id + 1
            self.team_id = f"T-{new_id:02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.team_name} (Created by: {self.creator.name})"

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"

class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    participant = models.OneToOneField(UserRegistration, on_delete=models.CASCADE, related_name='team_membership')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.participant.name} in {self.team.team_name}"

    class Meta:
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

class RoundNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('ROUND2_SELECTED', 'Round 2 Shortlisted'),
        ('ROUND2_NOT_SELECTED', 'Round 2 Not Shortlisted'),
        ('ROUND3_SELECTED', 'Round 3 Shortlisted'),
    )
    participant = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.participant.name}: {self.notification_type}"

class Round3Submission(models.Model):
    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='round3_submission')
    uploaded_by = models.ForeignKey(UserRegistration, on_delete=models.SET_NULL, null=True)
    ppt_file = models.FileField(upload_to='round3_submissions/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PPT for Team {self.team.team_id}"

class RoundTimingSettings(models.Model):
    team_formation_start = models.DateTimeField(null=True, blank=True)
    team_formation_end = models.DateTimeField(null=True, blank=True)
    ppt_submission_start = models.DateTimeField(null=True, blank=True)
    ppt_submission_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Round Timing Setting"
        verbose_name_plural = "Round Timing Settings"

    def __str__(self):
        return "Global Round Timing Settings"

    @classmethod
    def get_settings(cls):
        return cls.objects.first() or cls.objects.create()

    def get_team_formation_status(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.team_formation_start or now < self.team_formation_start:
            return "LOCKED"
        if self.team_formation_end and now > self.team_formation_end:
            return "CLOSED"
        return "OPEN"

    def get_ppt_submission_status(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.ppt_submission_start or now < self.ppt_submission_start:
            return "LOCKED"
        if self.ppt_submission_end and now > self.ppt_submission_end:
            return "CLOSED"
        return "OPEN"
