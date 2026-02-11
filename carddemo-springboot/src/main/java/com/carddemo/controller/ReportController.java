package com.carddemo.controller;

import com.carddemo.dto.ReportRequest;
import com.carddemo.entity.Transaction;
import com.carddemo.service.ReportService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/reports")
@Tag(name = "Reports")
public class ReportController {

    private final ReportService reportService;

    public ReportController(ReportService reportService) {
        this.reportService = reportService;
    }

    @PostMapping("/transactions")
    @Operation(summary = "Generate transaction report",
            description = "Generate a transaction detail report filtered by card number and date range. " +
                    "Equivalent to CORPT00C (Transaction CR00) which submits TRANREPT batch job. " +
                    "In the mainframe, this was a batch job (TRANREPT.jcl) that used SORT utility to filter " +
                    "transactions by date range. Here it returns results directly.")
    public ResponseEntity<Page<Transaction>> generateTransactionReport(
            @Valid @RequestBody ReportRequest request,
            @Parameter(description = "Card number to filter") @RequestParam String cardNumber,
            @Parameter(description = "Page number (0-based)") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "50") int size) {
        PageRequest pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.ASC, "cardNumber", "transactionId"));
        return ResponseEntity.ok(reportService.generateTransactionReport(request, cardNumber, pageable));
    }
}
