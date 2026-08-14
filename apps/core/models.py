from django.db import models
from django.contrib.auth.models import AbstractUser


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser, TimeStampedModel):
    class Role(models.TextChoices):
        PROCUREMENT_OFFICER = 'PROCUREMENT_OFFICER', 'Procurement Officer'
        MANAGER = 'MANAGER', 'Manager'
        CFO = 'CFO', 'Chief Financial Officer'
        ADMIN = 'ADMIN', 'Organization Admin'

    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)

    # Multi-Tenant Organization Link
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'
    )

    # Corporate Role & Spending Limit
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.PROCUREMENT_OFFICER
    )
    spending_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
