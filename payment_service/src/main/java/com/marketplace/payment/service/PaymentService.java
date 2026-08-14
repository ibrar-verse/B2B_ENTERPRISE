package com.marketplace.payment.service;

import com.marketplace.payment.dto.PaymentRequestDTO;
import com.marketplace.payment.dto.RefundRequestDTO;
import com.marketplace.payment.dto.SettlementRequestDTO;
import com.marketplace.payment.enums.EntryType;
import com.marketplace.payment.model.LedgerEntry;
import com.marketplace.payment.model.PaymentTransaction;
import com.marketplace.payment.repository.LedgerEntryRepository;
import com.marketplace.payment.repository.PaymentTransactionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
public class PaymentService {

    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);

    private final PaymentTransactionRepository transactionRepository;
    private final LedgerEntryRepository ledgerEntryRepository;

    public PaymentService(PaymentTransactionRepository transactionRepository,
                          LedgerEntryRepository ledgerEntryRepository) {
        this.transactionRepository = transactionRepository;
        this.ledgerEntryRepository = ledgerEntryRepository;
    }

    @Transactional
    public Map<String, Object> processPayment(PaymentRequestDTO dto) {
        Optional<PaymentTransaction> existingTxn = transactionRepository.findByIdempotencyKey(dto.getIdempotencyKey());
        if (existingTxn.isPresent()) {
            PaymentTransaction txn = existingTxn.get();
            log.warn("Duplicate payment request for key: {}. Returning cached response.", dto.getIdempotencyKey());
            return buildResponse(txn, true);
        }

        String gatewayRef = "TXN-" + UUID.randomUUID().toString().substring(0, 12).toUpperCase();

        PaymentTransaction transaction = new PaymentTransaction();
        transaction.setIdempotencyKey(dto.getIdempotencyKey());
        transaction.setOrderId(dto.getOrderId());
        transaction.setBuyerOrgId(dto.getBuyerOrgId());
        transaction.setVendorOrgId(dto.getVendorOrgId());
        transaction.setAmount(dto.getAmount());
        transaction.setCurrency(dto.getCurrency());
        transaction.setPaymentMethod(dto.getPaymentMethod());
        transaction.setStatus("SUCCESS");
        transaction.setGatewayReference(gatewayRef);
        PaymentTransaction savedTxn = transactionRepository.save(transaction);

        // Debit Escrow
        LedgerEntry debitEscrow = new LedgerEntry();
        debitEscrow.setTransactionId(savedTxn.getId());
        debitEscrow.setTransactionReference(gatewayRef);
        debitEscrow.setOrderId(dto.getOrderId());
        debitEscrow.setAccountType("ASSET");
        debitEscrow.setAccountNumber("ESCROW-" + dto.getPaymentMethod().toUpperCase());
        debitEscrow.setEntryType(EntryType.DEBIT);
        debitEscrow.setAmount(dto.getAmount());
        debitEscrow.setDescription("Escrow hold for Order #" + dto.getOrderId());
        ledgerEntryRepository.save(debitEscrow);

        // Credit Vendor Payable
        LedgerEntry creditPayable = new LedgerEntry();
        creditPayable.setTransactionId(savedTxn.getId());
        creditPayable.setTransactionReference(gatewayRef);
        creditPayable.setOrderId(dto.getOrderId());
        creditPayable.setAccountType("LIABILITY");
        creditPayable.setAccountNumber("VENDOR-PAYABLE-ORG-" + dto.getVendorOrgId());
        creditPayable.setEntryType(EntryType.CREDIT);
        creditPayable.setAmount(dto.getAmount());
        creditPayable.setDescription("Escrow liability obligation for Order #" + dto.getOrderId());
        ledgerEntryRepository.save(creditPayable);

        return buildResponse(savedTxn, false);
    }

    @Transactional
    public Map<String, Object> settleEscrow(SettlementRequestDTO dto) {
        String settlementRef = "SETTLE-" + UUID.randomUUID().toString().substring(0, 10).toUpperCase();

        // Debit Vendor Payable
        LedgerEntry debitPayable = new LedgerEntry();
        debitPayable.setTransactionId(0L);
        debitPayable.setTransactionReference(settlementRef);
        debitPayable.setOrderId(dto.getOrderId());
        debitPayable.setAccountType("LIABILITY");
        debitPayable.setAccountNumber("VENDOR-PAYABLE-ORG-" + dto.getVendorOrgId());
        debitPayable.setEntryType(EntryType.DEBIT);
        debitPayable.setAmount(dto.getAmount());
        debitPayable.setDescription("Escrow release settlement for Order #" + dto.getOrderId());
        ledgerEntryRepository.save(debitPayable);

        // Credit Vendor Wallet
        LedgerEntry creditWallet = new LedgerEntry();
        creditWallet.setTransactionId(0L);
        creditWallet.setTransactionReference(settlementRef);
        creditWallet.setOrderId(dto.getOrderId());
        creditWallet.setAccountType("EQUITY");
        creditWallet.setAccountNumber("VENDOR-WALLET-ORG-" + dto.getVendorOrgId());
        creditWallet.setEntryType(EntryType.CREDIT);
        creditWallet.setAmount(dto.getAmount());
        creditWallet.setDescription("Settled payout funds into wallet for Order #" + dto.getOrderId());
        ledgerEntryRepository.save(creditWallet);

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("orderId", dto.getOrderId());
        response.put("settlementReference", settlementRef);
        response.put("status", "SETTLED");
        return response;
    }

    @Transactional
    public Map<String, Object> processRefund(RefundRequestDTO dto) {
        Optional<PaymentTransaction> existingTxn = transactionRepository.findByIdempotencyKey(dto.getIdempotencyKey());
        if (existingTxn.isPresent()) {
            return buildResponse(existingTxn.get(), true);
        }

        String refundRef = "REFUND-" + UUID.randomUUID().toString().substring(0, 10).toUpperCase();

        PaymentTransaction refundTxn = new PaymentTransaction();
        refundTxn.setIdempotencyKey(dto.getIdempotencyKey());
        refundTxn.setOrderId(dto.getOrderId());
        refundTxn.setBuyerOrgId(0L);
        refundTxn.setVendorOrgId(dto.getVendorOrgId());
        refundTxn.setAmount(dto.getAmount());
        refundTxn.setCurrency("PKR");
        refundTxn.setPaymentMethod(dto.getPaymentMethod());
        refundTxn.setStatus("REFUNDED");
        refundTxn.setGatewayReference(refundRef);
        PaymentTransaction savedTxn = transactionRepository.save(refundTxn);

        // Debit Vendor Payable
        LedgerEntry debitPayable = new LedgerEntry();
        debitPayable.setTransactionId(savedTxn.getId());
        debitPayable.setTransactionReference(refundRef);
        debitPayable.setOrderId(dto.getOrderId());
        debitPayable.setAccountType("LIABILITY");
        debitPayable.setAccountNumber("VENDOR-PAYABLE-ORG-" + dto.getVendorOrgId());
        debitPayable.setEntryType(EntryType.DEBIT);
        debitPayable.setAmount(dto.getAmount());
        debitPayable.setDescription("Refund Reversal: " + dto.getReason() + " for Order #" + dto.getOrderId());
        ledgerEntryRepository.save(debitPayable);

        // Credit Escrow
        LedgerEntry creditEscrow = new LedgerEntry();
        creditEscrow.setTransactionId(savedTxn.getId());
        creditEscrow.setTransactionReference(refundRef);
        creditEscrow.setOrderId(dto.getOrderId());
        creditEscrow.setAccountType("ASSET");
        creditEscrow.setAccountNumber("ESCROW-" + dto.getPaymentMethod().toUpperCase());
        creditEscrow.setEntryType(EntryType.CREDIT);
        creditEscrow.setAmount(dto.getAmount());
        creditEscrow.setDescription("Refund Outbound to Gateway for Order #" + dto.getOrderId());
        ledgerEntryRepository.save(creditEscrow);

        return buildResponse(savedTxn, false);
    }

    private Map<String, Object> buildResponse(PaymentTransaction txn, boolean isDuplicate) {
        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("isDuplicate", isDuplicate);
        response.put("transactionId", txn.getId());
        response.put("orderId", txn.getOrderId());
        response.put("gatewayReference", txn.getGatewayReference());
        response.put("amount", txn.getAmount());
        response.put("status", txn.getStatus());
        return response;
    }
}