"""
User profile with role: farmer, microfinance, or admin.
Admin users are created in the backend (Django admin / management command) and use login only.
"""
from django.conf import settings
from django.db import models

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
