package com.carddemo.controller;

import com.carddemo.dto.AccountDetailDto;
import com.carddemo.dto.AccountUpdateRequest;
import com.carddemo.service.AccountService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/accounts")
@Tag(name = "Accounts")
public class AccountController {

    private final AccountService accountService;

    public AccountController(AccountService accountService) {
        this.accountService = accountService;
    }

    @GetMapping("/{acctId}")
    @Operation(summary = "View account details",
            description = "Retrieve account details including customer info and associated cards. " +
                    "Equivalent to COACTVWC (Transaction CAVW). " +
                    "Reads from ACCTDAT, CUSTDAT, CARDDAT, CCXREF files.")
    public ResponseEntity<AccountDetailDto> getAccount(@PathVariable String acctId) {
        return ResponseEntity.ok(accountService.getAccountDetail(acctId));
    }

    @PutMapping("/{acctId}")
    @Operation(summary = "Update account",
            description = "Update account and customer information. " +
                    "Equivalent to COACTUPC (Transaction CAUP). " +
                    "Updates ACCTDAT and CUSTDAT files.")
    public ResponseEntity<AccountDetailDto> updateAccount(
            @PathVariable String acctId, @RequestBody AccountUpdateRequest request) {
        return ResponseEntity.ok(accountService.updateAccount(acctId, request));
    }
}
