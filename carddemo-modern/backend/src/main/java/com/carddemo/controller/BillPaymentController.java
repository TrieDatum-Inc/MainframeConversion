package com.carddemo.controller;

import com.carddemo.dto.BillPaymentRequest;
import com.carddemo.dto.BillPaymentResponse;
import com.carddemo.service.BillPaymentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/payments")
@Tag(name = "Bill Payment")
public class BillPaymentController {

    private final BillPaymentService billPaymentService;

    public BillPaymentController(BillPaymentService billPaymentService) {
        this.billPaymentService = billPaymentService;
    }

    @PostMapping("/bill-pay")
    @Operation(summary = "Pay account balance in full",
            description = "Process a bill payment that pays the entire current balance. " +
                    "Equivalent to COBIL00C (Transaction CB00). " +
                    "Creates a payment transaction in TRANSACT file, then updates account balance in ACCTDAT to zero. " +
                    "Rejects if balance is zero or negative.")
    public ResponseEntity<BillPaymentResponse> payBill(@Valid @RequestBody BillPaymentRequest request) {
        return ResponseEntity.ok(billPaymentService.payBill(request));
    }
}
