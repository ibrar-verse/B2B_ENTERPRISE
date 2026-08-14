import hashlib
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PaymentGatewayClient:
    """
    Client service to communicate with the Spring Boot Payment & Ledger Microservice (Port 8080).
    """
    BASE_URL = getattr(settings, "PAYMENT_SERVICE_URL", "http://localhost:8080/api/v1/payments")

    @classmethod
    def generate_idempotency_key(cls, order_id: int, action: str) -> str:
        """Generates a deterministic unique key for a given order and action."""
        raw_key = f"order-{order_id}-{action}"
        return f"IDEMP-{hashlib.sha256(raw_key.encode()).hexdigest()[:24].upper()}"

    @classmethod
    def process_order_payment(cls, order, payment_method="JAZZCASH"):
        endpoint = f"{cls.BASE_URL}/process"
        idempotency_key = cls.generate_idempotency_key(order.id, "PAYMENT")

        payload = {
            "idempotencyKey": idempotency_key,
            "orderId": order.id,
            "buyerOrgId": order.buyer.id,
            "vendorOrgId": order.vendor.id,
            "amount": float(order.total_amount),
            "currency": "PKR",
            "paymentMethod": payment_method
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=5)
            if response.status_code in (200, 201):
                data = response.json()
                return {
                    "success": True,
                    "gateway_reference": data.get("gatewayReference"),
                    "is_duplicate": data.get("isDuplicate", False),
                    "status": data.get("status")
                }
            return {"success": False, "error": response.text}
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment microservice error for order #{order.id}: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def settle_vendor_escrow(cls, order):
        endpoint = f"{cls.BASE_URL}/settle"
        payload = {
            "orderId": order.id,
            "vendorOrgId": order.vendor.id,
            "amount": float(order.total_amount)
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=5)
            if response.status_code in (200, 201):
                data = response.json()
                return {
                    "success": True,
                    "settlement_reference": data.get("settlementReference"),
                    "status": data.get("status")
                }
            return {"success": False, "error": response.text}
        except requests.exceptions.RequestException as e:
            logger.error(f"Settlement failed for Order #{order.id}: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def process_order_refund(cls, order, reason="Buyer Order Cancellation"):
        endpoint = f"{cls.BASE_URL}/refund"
        idempotency_key = cls.generate_idempotency_key(order.id, "REFUND")

        payload = {
            "idempotencyKey": idempotency_key,
            "orderId": order.id,
            "vendorOrgId": order.vendor.id,
            "amount": float(order.total_amount),
            "paymentMethod": "JAZZCASH",
            "reason": reason
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=5)
            if response.status_code in (200, 201):
                data = response.json()
                return {
                    "success": True,
                    "refund_reference": data.get("gatewayReference"),
                    "status": data.get("status")
                }
            return {"success": False, "error": response.text}
        except requests.exceptions.RequestException as e:
            logger.error(f"Refund request failed for order #{order.id}: {e}")
            return {"success": False, "error": str(e)}
