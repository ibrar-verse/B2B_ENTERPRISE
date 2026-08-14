package com.marketplace.payment.repository;

import com.marketplace.payment.model.LedgerEntry;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface LedgerEntryRepository extends JpaRepository<LedgerEntry, Long> {
    List<LedgerEntry> findByOrderId(Long orderId);
    List<LedgerEntry> findByTransactionReference(String transactionReference);
    List<LedgerEntry> findByAccountNumber(String accountNumber);
}