package com.carddemo.controller;

import com.carddemo.dto.TransactionAddRequest;
import com.carddemo.entity.Transaction;
import com.carddemo.service.TransactionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/transactions")
@Tag(name = "Transactions")
public class TransactionController {

    private final TransactionService transactionService;

    public TransactionController(TransactionService transactionService) {
        this.transactionService = transactionService;
    }

    @GetMapping
    @Operation(summary = "List transactions (paginated)",
            description = "List all transactions with optional card number filter. " +
                    "Equivalent to COTRN00C (Transaction CT00). " +
                    "Reads from TRANSACT file.")
    public ResponseEntity<Page<Transaction>> listTransactions(
            @Parameter(description = "Filter by card number") @RequestParam(required = false) String cardNumber,
            @Parameter(description = "Page number (0-based)") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "10") int size) {
        PageRequest pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "transactionId"));
        if (cardNumber != null && !cardNumber.isBlank()) {
            return ResponseEntity.ok(transactionService.listTransactionsByCardNumber(cardNumber, pageable));
        }
        return ResponseEntity.ok(transactionService.listTransactions(pageable));
    }

    @GetMapping("/{transactionId}")
    @Operation(summary = "View single transaction",
            description = "Retrieve details for a specific transaction. " +
                    "Equivalent to COTRN01C (Transaction CT01). " +
                    "Reads from TRANSACT file.")
    public ResponseEntity<Transaction> getTransaction(@PathVariable String transactionId) {
        return ResponseEntity.ok(transactionService.getTransaction(transactionId));
    }

    @PostMapping
    @Operation(summary = "Add new transaction",
            description = "Create a new transaction record. Provide either accountId or cardNumber. " +
                    "Equivalent to COTRN02C (Transaction CT02). " +
                    "Validates card/account via CCXREF/CXACAIX, writes to TRANSACT file. " +
                    "Transaction ID is auto-generated (last ID + 1).")
    public ResponseEntity<Transaction> addTransaction(@Valid @RequestBody TransactionAddRequest request) {
        Transaction transaction = transactionService.addTransaction(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(transaction);
    }
}
