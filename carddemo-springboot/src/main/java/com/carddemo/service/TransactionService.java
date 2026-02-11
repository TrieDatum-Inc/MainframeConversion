package com.carddemo.service;

import com.carddemo.dto.TransactionAddRequest;
import com.carddemo.entity.CardXref;
import com.carddemo.entity.Transaction;
import com.carddemo.exception.BadRequestException;
import com.carddemo.exception.ResourceNotFoundException;
import com.carddemo.repository.CardXrefRepository;
import com.carddemo.repository.TransactionRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;

@Service
public class TransactionService {

    private final TransactionRepository transactionRepository;
    private final CardXrefRepository cardXrefRepository;

    public TransactionService(TransactionRepository transactionRepository, CardXrefRepository cardXrefRepository) {
        this.transactionRepository = transactionRepository;
        this.cardXrefRepository = cardXrefRepository;
    }

    public Page<Transaction> listTransactions(Pageable pageable) {
        return transactionRepository.findAll(pageable);
    }

    public Page<Transaction> listTransactionsByCardNumber(String cardNumber, Pageable pageable) {
        return transactionRepository.findByCardNumber(cardNumber, pageable);
    }

    public Transaction getTransaction(String transactionId) {
        return transactionRepository.findById(transactionId)
                .orElseThrow(() -> new ResourceNotFoundException("Transaction ID NOT found..."));
    }

    @Transactional
    public Transaction addTransaction(TransactionAddRequest request) {
        String cardNumber = resolveCardNumber(request);

        validateDate(request.getOriginDate(), "Orig Date - Not a valid date...");
        validateDate(request.getProcessDate(), "Proc Date - Not a valid date...");

        String newId = generateNextTransactionId();

        Transaction transaction = new Transaction();
        transaction.setTransactionId(newId);
        transaction.setTypeCode(request.getTypeCode());
        transaction.setCategoryCode(request.getCategoryCode());
        transaction.setSource(request.getSource());
        transaction.setDescription(request.getDescription());
        transaction.setAmount(request.getAmount());
        transaction.setCardNumber(cardNumber);
        transaction.setMerchantId(request.getMerchantId());
        transaction.setMerchantName(request.getMerchantName());
        transaction.setMerchantCity(request.getMerchantCity());
        transaction.setMerchantZip(request.getMerchantZip());
        transaction.setOriginTimestamp(request.getOriginDate());
        transaction.setProcessTimestamp(request.getProcessDate());

        return transactionRepository.save(transaction);
    }

    private String resolveCardNumber(TransactionAddRequest request) {
        if (request.getAccountId() != null && !request.getAccountId().isBlank()) {
            CardXref xref = cardXrefRepository.findFirstByAccountId(request.getAccountId())
                    .orElseThrow(() -> new ResourceNotFoundException("Account ID NOT found..."));
            return xref.getCardNumber();
        } else if (request.getCardNumber() != null && !request.getCardNumber().isBlank()) {
            cardXrefRepository.findById(request.getCardNumber())
                    .orElseThrow(() -> new ResourceNotFoundException("Card Number NOT found..."));
            return request.getCardNumber();
        } else {
            throw new BadRequestException("Account or Card Number must be entered...");
        }
    }

    private void validateDate(String dateStr, String errorMessage) {
        try {
            LocalDate.parse(dateStr, DateTimeFormatter.ISO_LOCAL_DATE);
        } catch (DateTimeParseException e) {
            throw new BadRequestException(errorMessage);
        }
    }

    private synchronized String generateNextTransactionId() {
        String maxId = transactionRepository.findMaxTransactionId().orElse("0000000000000000");
        long nextId = Long.parseLong(maxId.trim()) + 1;
        return String.format("%016d", nextId);
    }
}
