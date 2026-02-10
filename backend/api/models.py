"""
User profile with role: farmer, microfinance, or admin.
Admin users are created in the backend (Django admin / management command) and use login only.
"""
import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone

ROLE_CHOICES = [
    ('farmer', 'Farmer'),
    ('microfinance', 'Microfinance'),
    ('admin', 'Admin'),
]


class UserProfile(models.Model):
    """Extended profile: links User to role (farmer, microfinance, admin)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agrifin_profile',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        db_table = 'api_userprofile'

    def __str__(self):
        return f"{self.user.username} ({self.role})"


EVENT_TYPE_CHOICES = [
    ('modal_opened', 'Modal opened'),
    ('register_clicked', 'Register clicked'),
    ('login_clicked', 'Login clicked'),
]


class GetStartedEvent(models.Model):
    """Logs Get Started modal activity for admin analytics. Visitors trigger events without auth."""
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    role = models.CharField(max_length=20, default='')  # farmers, microfinances, admin
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'api_getstartedevent'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} ({self.role}) at {self.created_at}"


def _default_token_expiry():
    return timezone.now() + timezone.timedelta(hours=1)


class PasswordResetToken(models.Model):
    """One-time token for password reset. Expires after 1 hour."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=_default_token_expiry)

    class Meta:
        db_table = 'api_passwordresettoken'
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset for {self.user.email} expires {self.expires_at}"

    @classmethod
    def create_for_user(cls, user):
        """Create a new reset token for user. Invalidates previous tokens."""
        cls.objects.filter(user=user).delete()
        token = secrets.token_urlsafe(32)
        return cls.objects.create(user=user, token=token)

    @classmethod
    def get_valid_user(cls, token):
        """Return user if token is valid and not expired, else None."""
        now = timezone.now()
        try:
            prt = cls.objects.get(token=token, expires_at__gt=now)
            user = prt.user
            prt.delete()  # One-time use
            return user
        except cls.DoesNotExist:
            return None


# ----- Loan workflow models (per system analysis ERD) -----

class FarmerProfile(models.Model):
    """Extended profile for farmers: location, phone, agricultural context."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='farmer_profile',
    )
    location = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    cooperative_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_farmerprofile'

    def __str__(self):
        return f"Farmer {self.user.username}"


class AgriculturalRecord(models.Model):
    """Farm records: crops, yields, land size for credit assessment."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agricultural_records',
    )
    crop_type = models.CharField(max_length=100)
    land_size_hectares = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_yield = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    season = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'api_agriculturalrecord'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.crop_type} ({self.user.username})"


LOAN_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]


class LoanApplication(models.Model):
    """
    Loan application with ML-derived eligibility, risk, and recommended amount.
    Maps farmer input to ML model features.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loan_applications',
    )
    # Application inputs (mapped to ML features)
    age = models.PositiveIntegerField(default=35)
    annual_income = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit_score = models.PositiveIntegerField(default=600)
    loan_amount_requested = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    loan_duration_months = models.PositiveIntegerField(default=24)
    employment_status = models.CharField(max_length=30, default='Self-Employed')
    education_level = models.CharField(max_length=30, default='High School')
    marital_status = models.CharField(max_length=20, default='Married')
    loan_purpose = models.CharField(max_length=50, default='Other')
    # AI outputs
    eligibility_approved = models.BooleanField(null=True, blank=True)
    eligibility_reason = models.TextField(blank=True)
    risk_score = models.FloatField(null=True, blank=True)
    recommended_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    # Status and review
    status = models.CharField(max_length=20, choices=LOAN_STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_loanapplication'
        ordering = ['-created_at']

    def __str__(self):
        return f"Loan #{self.id} ({self.user.username})"


class Loan(models.Model):
    """Approved loan with repayment schedule."""
    application = models.OneToOneField(
        LoanApplication,
        on_delete=models.CASCADE,
        related_name='approved_loan',
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0.12)
    duration_months = models.PositiveIntegerField()
    monthly_payment = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'api_loan'
        ordering = ['-created_at']

    def __str__(self):
        return f"Loan #{self.id} ({self.amount})"


class Repayment(models.Model):
    """Individual repayment record for a loan."""
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='repayments',
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')  # pending, paid, overdue
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'api_repayment'
        ordering = ['due_date']

    def __str__(self):
        return f"Repayment {self.amount} ({self.loan_id})"


class ChatInteraction(models.Model):
    """Log chatbot interactions for analytics and audit."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_interactions',
    )
    message = models.TextField()
    reply = models.TextField()
    language = models.CharField(max_length=5, default='en')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'api_chatinteraction'
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat {self.id}"
