package com.carddemo.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class BillPaymentRequest {

    @NotBlank(message = "Account ID is required")
    @Size(max = 11, message = "Account ID must be at most 11 characters")
    private String accountId;

    public String getAccountId() { return accountId; }
    public void setAccountId(String accountId) { this.accountId = accountId; }
}
