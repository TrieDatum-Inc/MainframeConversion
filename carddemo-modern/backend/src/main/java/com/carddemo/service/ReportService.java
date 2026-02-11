package com.carddemo.service;

import com.carddemo.dto.ReportRequest;
import com.carddemo.entity.Transaction;
import com.carddemo.repository.TransactionRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
public class ReportService {

    private final TransactionRepository transactionRepository;

    public ReportService(TransactionRepository transactionRepository) {
        this.transactionRepository = transactionRepository;
    }

    public Page<Transaction> generateTransactionReport(ReportRequest request, String cardNumber, Pageable pageable) {
        return transactionRepository.findByCardNumberAndDateRange(
                cardNumber,
                request.getStartDate(),
                request.getEndDate(),
                pageable
        );
    }
}
