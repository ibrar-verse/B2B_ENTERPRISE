package com.marketplace.payment.dto;

import com.marketplace.payment.enums.PaymentMethod;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

public class PaymentRequest {

    @NotNull(message = "Order ID is mandatory")
    private Long orderId;

    @NotNull(message = "Buyer Organization ID is mandatory")
    private Long buyerOrgId;

    @NotNull(message = "Vendor Organization ID is mandatory")
    private Long vendorOrgId;

    @NotNull(message = "Amount is mandatory")
    @DecimalMin(value = "0.01", message = "Amount must be greater than zero")
    private BigDecimal amount;

    private String currency = "PKR";

    @NotNull(message = "Payment method is mandatory")
    private PaymentMethod paymentMethod;

    public PaymentRequest() {}

    // Getters & Setters
    public Long getOrderId() { return orderId; }
    public void setOrderId(Long orderId) { this.orderId = orderId; }

    public Long getBuyerOrgId() { return buyerOrgId; }
    public void setBuyerOrgId(Long buyerOrgId) { this.buyerOrgId = buyerOrgId; }

    public Long getVendorOrgId() { return vendorOrgId; }
    public void setVendorOrgId(Long vendorOrgId) { this.vendorOrgId = vendorOrgId; }

    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }

    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }

    public PaymentMethod getPaymentMethod() { return paymentMethod; }
    public void setPaymentMethod(PaymentMethod paymentMethod) { this.paymentMethod = paymentMethod; }
}