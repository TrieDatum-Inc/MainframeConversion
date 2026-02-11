package com.carddemo.controller;

import com.carddemo.dto.TransactionTypeUpdateRequest;
import com.carddemo.entity.TransactionCategory;
import com.carddemo.entity.TransactionType;
import com.carddemo.service.TransactionTypeService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/admin/transaction-types")
@PreAuthorize("hasRole('ADMIN')")
@Tag(name = "Admin - Transaction Types")
public class TransactionTypeController {

    private final TransactionTypeService transactionTypeService;

    public TransactionTypeController(TransactionTypeService transactionTypeService) {
        this.transactionTypeService = transactionTypeService;
    }

    @GetMapping
    @Operation(summary = "List transaction types (paginated)",
            description = "List all transaction types. Admin only. " +
                    "Equivalent to COTRTLIC (Transaction CTLI). " +
                    "Reads from DB2 TRANSACTION_TYPE table.")
    public ResponseEntity<Page<TransactionType>> listTransactionTypes(
            @Parameter(description = "Page number (0-based)") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(transactionTypeService.listTransactionTypes(PageRequest.of(page, size)));
    }

    @GetMapping("/{typeCode}")
    @Operation(summary = "Get transaction type details",
            description = "Get a specific transaction type and its categories.")
    public ResponseEntity<TransactionType> getTransactionType(@PathVariable String typeCode) {
        return ResponseEntity.ok(transactionTypeService.getTransactionType(typeCode));
    }

    @GetMapping("/{typeCode}/categories")
    @Operation(summary = "List categories for a transaction type",
            description = "List all categories within a transaction type. " +
                    "Reads from DB2 TRANSACTION_CATEGORY table.")
    public ResponseEntity<List<TransactionCategory>> getCategories(@PathVariable String typeCode) {
        return ResponseEntity.ok(transactionTypeService.getCategoriesByType(typeCode));
    }

    @PutMapping("/{typeCode}")
    @Operation(summary = "Update transaction type",
            description = "Update a transaction type description. Admin only. " +
                    "Equivalent to COTRTUPC (Transaction CTTU). " +
                    "Updates DB2 TRANSACTION_TYPE table.")
    public ResponseEntity<TransactionType> updateTransactionType(
            @PathVariable String typeCode, @Valid @RequestBody TransactionTypeUpdateRequest request) {
        return ResponseEntity.ok(transactionTypeService.updateTransactionType(typeCode, request));
    }
}
