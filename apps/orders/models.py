from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.organizations.models import Organization


class Product(models.Model):
    vendor = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='products',
        limit_choices_to={'org_type__in': ['VENDOR', 'BOTH']}
    )
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, default="General")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    min_order_qty = models.PositiveIntegerField(default=1)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.sku} - {self.name} ({self.vendor.name})"


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        APPROVED = 'APPROVED', _('Approved')
        PAID = 'PAID', _('Paid (Escrow Locked)')
        COMPLETED = 'COMPLETED', _('Completed (Settled)')
        CANCELLED = 'CANCELLED', _('Cancelled / Refunded')

    buyer = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='purchase_orders',
        limit_choices_to={'org_type__in': ['BUYER', 'BOTH']}
    )
    vendor = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='sales_orders',
        limit_choices_to={'org_type__in': ['VENDOR', 'BOTH']}
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_orders'
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    payment_reference = models.CharField(max_length=128, blank=True, null=True)
    settlement_reference = models.CharField(max_length=128, blank=True, null=True)
    refund_reference = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} | {self.buyer.name} -> {self.vendor.name} ({self.status})"

    def execute_payment(self, payment_method="JAZZCASH"):
        """Locks funds into platform escrow via payment gateway client."""
        if self.status != self.Status.APPROVED:
            return False

        from .services import PaymentGatewayClient
        result = PaymentGatewayClient.charge_escrow(self, payment_method=payment_method)

        if result.get("success"):
            self.status = self.Status.PAID
            self.payment_reference = result.get("payment_reference", "MOCK-PAY-OK")
            self.save(update_fields=["status", "payment_reference", "updated_at"])
            return True
        return False

    def complete_order(self):
        """Releases locked escrow balance to the vendor organization."""
        if self.status != self.Status.PAID:
            return False

        from .services import PaymentGatewayClient
        result = PaymentGatewayClient.settle_vendor_escrow(self)

        if result.get("success"):
            self.status = self.Status.COMPLETED
            self.settlement_reference = result.get("settlement_reference", "SETTLE-OK")
            self.save(update_fields=["status", "settlement_reference", "updated_at"])
            return True
        return False

    def cancel_and_refund(self, reason="Buyer dispute / non-delivery"):
        """Refunds escrow funds back to buyer and cancels order."""
        if self.status not in [self.Status.APPROVED, self.Status.PAID]:
            return False

        from .services import PaymentGatewayClient
        result = PaymentGatewayClient.refund_escrow(self, reason=reason)

        if result.get("success"):
            self.status = self.Status.CANCELLED
            self.refund_reference = result.get("refund_reference", "REFUND-OK")
            self.save(update_fields=["status", "refund_reference", "updated_at"])
            return self.refund_reference
        return False