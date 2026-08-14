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
    def process_order_payment(cls, order, payment_method="JAZZCASH"):
        endpoint = f"{cls.BASE_URL}/process"

        payload = {
            "orderId": order.id,
            "buyerOrgId": order.buyer.id,
            "vendorOrgId": order.vendor.id,
            "amount": float(order.total_amount),
            "currency": "PKR",
            "paymentMethod": payment_method
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=5)

            if response.status_code == 201:
                data = response.json()
                logger.info(f"Payment successful for Order #{order.id}: TXN {data.get('gatewayReference')}")
                return {
                    "success": True,
                    "gateway_reference": data.get("gatewayReference"),
                    "status": data.get("status")
                }
            else:
                logger.error(f"Payment service error for order #{order.id}: {response.text}")
                return {
                    "success": False,
                    "error": f"Service returned status {response.status_code}"
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Payment Microservice connection failed: {str(e)}")
            return {
                "success": False,
                "error": "Payment microservice unreachable on port 8080"
            }