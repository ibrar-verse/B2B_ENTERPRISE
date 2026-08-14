package com.marketplace.payment.controller;

import com.marketplace.payment.dto.PaymentRequestDTO;
import com.marketplace.payment.dto.RefundRequestDTO;
import com.marketplace.payment.dto.SettlementRequestDTO;
import com.marketplace.payment.service.PaymentService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class PaymentController {

    private final PaymentService paymentService;

    public PaymentController(PaymentService paymentService) {
        this.paymentService = paymentService;
    }

    @PostMapping("/process")
    public ResponseEntity<Map<String, Object>> processPayment(@Valid @RequestBody PaymentRequestDTO request) {
        Map<String, Object> response = paymentService.processPayment(request);
        return new ResponseEntity<>(response, HttpStatus.CREATED);
    }

    @PostMapping("/settle")
    public ResponseEntity<Map<String, Object>> settleOrder(@Valid @RequestBody SettlementRequestDTO request) {
        Map<String, Object> response = paymentService.settleEscrow(request);
        return new ResponseEntity<>(response, HttpStatus.OK);
    }

    @PostMapping("/refund")
    public ResponseEntity<Map<String, Object>> refundOrder(@Valid @RequestBody RefundRequestDTO request) {
        Map<String, Object> response = paymentService.processRefund(request);
        return new ResponseEntity<>(response, HttpStatus.OK);
    }
}