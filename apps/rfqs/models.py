from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class RFQ(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        OPEN = 'OPEN', 'Open'
        CLOSED = 'CLOSED', 'Closed'
        AWARDED = 'AWARDED', 'Awarded'

    title = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        default=0.00
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    buyer_organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='rfqs'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_rfqs'
    )
    closing_date = models.DateTimeField()

    def __str__(self):
        return f"RFQ: {self.title} ({self.buyer_organization.name})"


class Bid(TimeStampedModel):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'

    rfq = models.ForeignKey(
        RFQ,
        on_delete=models.CASCADE,
        related_name='bids'
    )
    vendor_organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='submitted_bids'
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_submitted_bids'
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED
    )

    def save(self, *args, **kwargs):
        # Auto-calculate total price before saving to database
        if self.unit_price and self.rfq and self.rfq.quantity:
            self.total_price = self.unit_price * self.rfq.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bid ${self.total_price} for {self.rfq.title} by {self.vendor_organization.name}"