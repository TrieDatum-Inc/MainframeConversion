package com.carddemo.dto;

import java.math.BigDecimal;

public class BillPaymentResponse {

    private String transactionId;
    private String accountId;
    private BigDecimal amountPaid;
    private BigDecimal newBalance;
    private String message;

    public BillPaymentResponse() {}

    public BillPaymentResponse(String transactionId, String accountId, BigDecimal amountPaid, BigDecimal newBalance, String message) {
        this.transactionId = transactionId;
        this.accountId = accountId;
        this.amountPaid = amountPaid;
        this.newBalance = newBalance;
        this.message = message;
    }

    public String getTransactionId() { return transactionId; }
    public void setTransactionId(String transactionId) { this.transactionId = transactionId; }
    public String getAccountId() { return accountId; }
    public void setAccountId(String accountId) { this.accountId = accountId; }
    public BigDecimal getAmountPaid() { return amountPaid; }
    public void setAmountPaid(BigDecimal amountPaid) { this.amountPaid = amountPaid; }
    public BigDecimal getNewBalance() { return newBalance; }
    public void setNewBalance(BigDecimal newBalance) { this.newBalance = newBalance; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
}
