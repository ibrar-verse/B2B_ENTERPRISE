from django.db import models
from apps.core.models import TimeStampedModel


class Organization(TimeStampedModel):
    class OrgType(models.TextChoices):
        BUYER = 'BUYER', 'Corporate Buyer'
        VENDOR = 'VENDOR', 'Wholesale Vendor'
        BOTH = 'BOTH', 'Buyer & Vendor'

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    org_type = models.CharField(
        max_length=20,
        choices=OrgType.choices,
        default=OrgType.BUYER
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name