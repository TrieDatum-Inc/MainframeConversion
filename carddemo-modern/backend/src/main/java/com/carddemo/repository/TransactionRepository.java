package com.carddemo.repository;

import com.carddemo.entity.Transaction;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface TransactionRepository extends JpaRepository<Transaction, String> {

    Page<Transaction> findByCardNumber(String cardNumber, Pageable pageable);

    Page<Transaction> findByCardNumberIn(java.util.List<String> cardNumbers, Pageable pageable);

    @Query("SELECT t FROM Transaction t ORDER BY t.transactionId DESC")
    Page<Transaction> findTopByOrderByTransactionIdDesc(Pageable pageable);

    @Query("SELECT MAX(t.transactionId) FROM Transaction t")
    Optional<String> findMaxTransactionId();

    @Query("SELECT t FROM Transaction t WHERE t.cardNumber = :cardNumber " +
           "AND t.originTimestamp >= :startDate AND t.originTimestamp <= :endDate")
    Page<Transaction> findByCardNumberAndDateRange(
            @Param("cardNumber") String cardNumber,
            @Param("startDate") String startDate,
            @Param("endDate") String endDate,
            Pageable pageable);
}
