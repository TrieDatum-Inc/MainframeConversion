package com.carddemo.service;

import com.carddemo.dto.BillPaymentRequest;
import com.carddemo.dto.BillPaymentResponse;
import com.carddemo.entity.Account;
import com.carddemo.entity.CardXref;
import com.carddemo.entity.Transaction;
import com.carddemo.exception.BadRequestException;
import com.carddemo.exception.ResourceNotFoundException;
import com.carddemo.repository.AccountRepository;
import com.carddemo.repository.CardXrefRepository;
import com.carddemo.repository.TransactionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Service
public class BillPaymentService {

    private final AccountRepository accountRepository;
    private final CardXrefRepository cardXrefRepository;
    private final TransactionRepository transactionRepository;

    public BillPaymentService(AccountRepository accountRepository,
                              CardXrefRepository cardXrefRepository,
                              TransactionRepository transactionRepository) {
        this.accountRepository = accountRepository;
        this.cardXrefRepository = cardXrefRepository;
        this.transactionRepository = transactionRepository;
    }

    @Transactional
    public BillPaymentResponse payBill(BillPaymentRequest request) {
        Account account = accountRepository.findById(request.getAccountId())
                .orElseThrow(() -> new ResourceNotFoundException("Account ID NOT found..."));

        if (account.getCurrentBalance() == null || account.getCurrentBalance().compareTo(BigDecimal.ZERO) <= 0) {
            throw new BadRequestException("You have nothing to pay...");
        }

        CardXref xref = cardXrefRepository.findFirstByAccountId(request.getAccountId())
                .orElseThrow(() -> new ResourceNotFoundException("Account ID NOT found in XREF..."));

        String newId = generateNextTransactionId();

        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSSSSS"));

        Transaction transaction = new Transaction();
        transaction.setTransactionId(newId);
        transaction.setTypeCode("02");
        transaction.setCategoryCode(2);
        transaction.setSource("POS TERM");
        transaction.setDescription("BILL PAYMENT - ONLINE");
        transaction.setAmount(account.getCurrentBalance());
        transaction.setCardNumber(xref.getCardNumber());
        transaction.setMerchantId("999999999");
        transaction.setMerchantName("BILL PAYMENT");
        transaction.setMerchantCity("N/A");
        transaction.setMerchantZip("N/A");
        transaction.setOriginTimestamp(timestamp);
        transaction.setProcessTimestamp(timestamp);

        transactionRepository.save(transaction);

        BigDecimal amountPaid = account.getCurrentBalance();
        account.setCurrentBalance(account.getCurrentBalance().subtract(amountPaid));
        accountRepository.save(account);

        return new BillPaymentResponse(
                newId,
                account.getAcctId(),
                amountPaid,
                account.getCurrentBalance(),
                "Bill payment processed successfully. Transaction ID: " + newId
        );
    }

    private synchronized String generateNextTransactionId() {
        String maxId = transactionRepository.findMaxTransactionId().orElse("0000000000000000");
        long nextId = Long.parseLong(maxId.trim()) + 1;
        return String.format("%016d", nextId);
    }
}
