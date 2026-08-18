from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

from apps.orders.models import Order, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "vendor",
        "category",
        "unit_price_formatted",
        "stock_quantity",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "is_active", "vendor")
    search_fields = ("name", "sku", "vendor__name", "category")
    list_editable = ("is_active", "stock_quantity")
    ordering = ("-created_at",)

    @admin.display(description="Unit Price")
    def unit_price_formatted(self, obj):
        return f"PKR {obj.unit_price:,.2f}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_form_template = "admin/orders/order/change_form.html"

    list_display = (
        "id",
        "buyer",
        "vendor",
        "total_amount_formatted",
        "status_badge",
        "payment_reference",
        "settlement_reference",
        "created_at",
    )
    list_filter = ("status", "buyer", "vendor", "created_at")
    search_fields = (
        "id",
        "buyer__name",
        "vendor__name",
        "payment_reference",
        "settlement_reference",
        "refund_reference",
    )
    readonly_fields = (
        "payment_reference",
        "settlement_reference",
        "refund_reference",
        "created_at",
        "updated_at",
    )
    actions = ["action_execute_payment", "action_settle_escrow", "action_refund_orders"]

    # ---------------------------------------------------------
    # Visual Enhancements
    # ---------------------------------------------------------
    @admin.display(description="Total Amount")
    def total_amount_formatted(self, obj):
        return f"PKR {obj.total_amount:,.2f}"

    @admin.display(description="Status")
    def status_badge(self, obj):
        color_map = {
            getattr(Order.Status, "DRAFT", "DRAFT"): "#6b7280",          # Gray
            getattr(Order.Status, "APPROVED", "APPROVED"): "#3b82f6",    # Blue
            getattr(Order.Status, "PAID", "PAID"): "#10b981",            # Emerald
            getattr(Order.Status, "COMPLETED", "COMPLETED"): "#059669",  # Dark Green
            getattr(Order.Status, "CANCELLED", "CANCELLED"): "#ef4444",  # Red
        }
        color = color_map.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    # ---------------------------------------------------------
    # Custom URLs for 1-Click Buttons
    # ---------------------------------------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:order_id>/process-payment/",
                self.admin_site.admin_view(self.process_payment_view),
                name="order-process-payment",
            ),
            path(
                "<int:order_id>/settle-escrow/",
                self.admin_site.admin_view(self.settle_escrow_view),
                name="order-settle-escrow",
            ),
            path(
                "<int:order_id>/refund/",
                self.admin_site.admin_view(self.refund_order_view),
                name="order-refund",
            ),
        ]
        return custom_urls + urls

    def process_payment_view(self, request, order_id):
        order = self.get_object(request, order_id)
        if not order:
            self.message_user(request, "Order not found.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:orders_order_changelist"))

        if order.status != Order.Status.APPROVED:
            self.message_user(
                request,
                f"Cannot pay Order #{order.id} in status '{order.status}'.",
                level=messages.WARNING,
            )
            return HttpResponseRedirect(
                reverse("admin:orders_order_change", args=[order.id])
            )

        success = order.execute_payment(payment_method="JAZZCASH")
        if success:
            self.message_user(
                request,
                f"✅ Order #{order.id} payment processed via Spring Boot! TXN Reference: {order.payment_reference}",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                f"❌ Payment failed for Order #{order.id}. Check microservice logs on port 8080.",
                level=messages.ERROR,
            )
        return HttpResponseRedirect(
            reverse("admin:orders_order_change", args=[order.id])
        )

    def settle_escrow_view(self, request, order_id):
        order = self.get_object(request, order_id)
        if not order:
            self.message_user(request, "Order not found.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:orders_order_changelist"))

        if order.status != Order.Status.PAID:
            self.message_user(
                request,
                f"Only PAID orders can be settled. Current status: '{order.status}'.",
                level=messages.WARNING,
            )
            return HttpResponseRedirect(
                reverse("admin:orders_order_change", args=[order.id])
            )

        try:
            success = order.complete_order()
            if success:
                self.message_user(
                    request,
                    f"🎉 Escrow released! PKR {order.total_amount:,.2f} settled to {order.vendor.name}. Ref: {order.settlement_reference}",
                    level=messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    f"❌ Settlement failed for Order #{order.id}.",
                    level=messages.ERROR,
                )
        except Exception as e:
            self.message_user(request, f"Error: {str(e)}", level=messages.ERROR)

        return HttpResponseRedirect(
            reverse("admin:orders_order_change", args=[order.id])
        )

    def refund_order_view(self, request, order_id):
        order = self.get_object(request, order_id)
        if not order:
            self.message_user(request, "Order not found.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:orders_order_changelist"))

        if order.status != Order.Status.PAID:
            self.message_user(
                request,
                f"Only PAID orders can be refunded. Current status: '{order.status}'.",
                level=messages.WARNING,
            )
            return HttpResponseRedirect(
                reverse("admin:orders_order_change", args=[order.id])
            )

        try:
            refund_ref = order.cancel_and_refund(reason="Admin Requested Refund via UI")
            if refund_ref:
                self.message_user(
                    request,
                    f"↩️ Order #{order.id} refunded and cancelled! Ledger reversal ref: {refund_ref}",
                    level=messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    f"❌ Refund failed for Order #{order.id}. Check microservice logs on port 8080.",
                    level=messages.ERROR,
                )
        except Exception as e:
            self.message_user(request, f"Error: {str(e)}", level=messages.ERROR)

        return HttpResponseRedirect(
            reverse("admin:orders_order_change", args=[order.id])
        )

    # ---------------------------------------------------------
    # Bulk Actions (List View Dropdown)
    # ---------------------------------------------------------
    @admin.action(description="⚡ Process Payment for selected APPROVED Orders")
    def action_execute_payment(self, request, queryset):
        approved_orders = queryset.filter(status=Order.Status.APPROVED)
        if not approved_orders.exists():
            self.message_user(
                request, "No APPROVED orders were selected.", level=messages.WARNING
            )
            return

        success_count = 0
        for order in approved_orders:
            if order.execute_payment(payment_method="JAZZCASH"):
                success_count += 1

        self.message_user(
            request,
            f"Successfully processed payment for {success_count} of {approved_orders.count()} order(s).",
            level=messages.SUCCESS if success_count else messages.ERROR,
        )

    @admin.action(description="💰 Settle Escrow for selected PAID Orders")
    def action_settle_escrow(self, request, queryset):
        paid_orders = queryset.filter(status=Order.Status.PAID)
        if not paid_orders.exists():
            self.message_user(
                request, "No PAID orders were selected.", level=messages.WARNING
            )
            return

        settled_count = 0
        for order in paid_orders:
            try:
                if order.complete_order():
                    settled_count += 1
            except Exception:
                continue

        self.message_user(
            request,
            f"Successfully settled escrow for {settled_count} of {paid_orders.count()} order(s).",
            level=messages.SUCCESS if settled_count else messages.ERROR,
        )

    @admin.action(description="↩️ Cancel & Refund selected PAID Orders")
    def action_refund_orders(self, request, queryset):
        paid_orders = queryset.filter(status=Order.Status.PAID)
        if not paid_orders.exists():
            self.message_user(
                request, "No PAID orders were selected for refund.", level=messages.WARNING
            )
            return

        refunded_count = 0
        for order in paid_orders:
            try:
                if order.cancel_and_refund(reason="Bulk Admin Refund Action"):
                    refunded_count += 1
            except Exception:
                continue

        self.message_user(
            request,
            f"Successfully refunded and cancelled {refunded_count} of {paid_orders.count()} order(s).",
            level=messages.SUCCESS if refunded_count else messages.ERROR,
        )