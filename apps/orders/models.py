from django.conf import settings
from django.db import models, transaction
from apps.common.models import TimeStampedModel
from apps.organizations.models import Organization

class Order(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        PAID = "PAID", "Paid"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    buyer = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="purchase_orders"
    )
    vendor = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="sales_orders"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_orders"
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    payment_reference = models.CharField(
        max_length=100, blank=True, null=True, help_text="Reference from Payment Service"
    )
    settlement_reference = models.CharField(
        max_length=100, blank=True, null=True, help_text="Reference from Settlement"
    )

    def __str__(self):
        return f"Order #{self.id} - {self.buyer.name} -> {self.vendor.name} ({self.status})"

    def execute_payment(self, payment_method="JAZZCASH"):
        """
        Executes payment under an atomic transaction with row-level locking.
        """
        with transaction.atomic():
            # Lock the order row to prevent race conditions
            locked_order = Order.objects.select_for_update().get(id=self.id)

            if locked_order.status != self.Status.APPROVED:
                return False

            from apps.orders.services import PaymentGatewayClient

            result = PaymentGatewayClient.process_order_payment(locked_order, payment_method=payment_method)
            if result.get("success"):
                locked_order.status = self.Status.PAID
                locked_order.payment_reference = result.get("gateway_reference")
                locked_order.save(update_fields=["status", "payment_reference", "updated_at"])
                self.status = locked_order.status
                self.payment_reference = locked_order.payment_reference
                return True
            return False

    def complete_order(self):
        """
        Completes order and settles escrow under an atomic transaction with row-level locking.
        """
        with transaction.atomic():
            locked_order = Order.objects.select_for_update().get(id=self.id)

            if locked_order.status != self.Status.PAID:
                raise ValueError("Only PAID orders can be completed and settled.")

            from apps.orders.services import PaymentGatewayClient

            result = PaymentGatewayClient.settle_vendor_escrow(locked_order)
            if result.get("success"):
                locked_order.status = self.Status.COMPLETED
                locked_order.settlement_reference = result.get("settlement_reference")
                locked_order.save(update_fields=["status", "settlement_reference", "updated_at"])
                self.status = locked_order.status
                self.settlement_reference = locked_order.settlement_reference
                return True
            return False

    def cancel_and_refund(self, reason="Admin Cancellation"):
        """
        Cancels a PAID order and executes reversing ledger entries in Spring Boot.
        """
        with transaction.atomic():
            locked_order = Order.objects.select_for_update().get(id=self.id)

            if locked_order.status != self.Status.PAID:
                raise ValueError(f"Cannot refund order in status '{locked_order.status}'. Only PAID orders can be refunded.")

            from apps.orders.services import PaymentGatewayClient

            result = PaymentGatewayClient.process_order_refund(locked_order, reason=reason)
            if result.get("success"):
                locked_order.status = self.Status.CANCELLED
                locked_order.save(update_fields=["status", "updated_at"])
                self.status = locked_order.status
                return result.get("refund_reference")
            return None