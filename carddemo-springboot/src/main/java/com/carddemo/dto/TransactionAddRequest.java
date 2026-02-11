package com.carddemo.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

public class TransactionAddRequest {

    @Size(max = 11, message = "Account ID must be at most 11 characters")
    private String accountId;

    @Size(max = 16, message = "Card number must be at most 16 characters")
    private String cardNumber;

    @NotBlank(message = "Type code is required")
    @Pattern(regexp = "\\d{2}", message = "Type code must be 2 digits")
    private String typeCode;

    @NotNull(message = "Category code is required")
    private Integer categoryCode;

    @NotBlank(message = "Source is required")
    @Size(max = 10, message = "Source must be at most 10 characters")
    private String source;

    @NotBlank(message = "Description is required")
    @Size(max = 100, message = "Description must be at most 100 characters")
    private String description;

    @NotNull(message = "Amount is required")
    private BigDecimal amount;

    @NotBlank(message = "Origination date is required")
    @Pattern(regexp = "\\d{4}-\\d{2}-\\d{2}", message = "Origination date must be in format YYYY-MM-DD")
    private String originDate;

    @NotBlank(message = "Processing date is required")
    @Pattern(regexp = "\\d{4}-\\d{2}-\\d{2}", message = "Processing date must be in format YYYY-MM-DD")
    private String processDate;

    @NotBlank(message = "Merchant ID is required")
    @Pattern(regexp = "\\d+", message = "Merchant ID must be numeric")
    @Size(max = 9, message = "Merchant ID must be at most 9 digits")
    private String merchantId;

    @NotBlank(message = "Merchant name is required")
    @Size(max = 50, message = "Merchant name must be at most 50 characters")
    private String merchantName;

    @NotBlank(message = "Merchant city is required")
    @Size(max = 50, message = "Merchant city must be at most 50 characters")
    private String merchantCity;

    @NotBlank(message = "Merchant zip is required")
    @Size(max = 10, message = "Merchant zip must be at most 10 characters")
    private String merchantZip;

    public String getAccountId() { return accountId; }
    public void setAccountId(String accountId) { this.accountId = accountId; }
    public String getCardNumber() { return cardNumber; }
    public void setCardNumber(String cardNumber) { this.cardNumber = cardNumber; }
    public String getTypeCode() { return typeCode; }
    public void setTypeCode(String typeCode) { this.typeCode = typeCode; }
    public Integer getCategoryCode() { return categoryCode; }
    public void setCategoryCode(Integer categoryCode) { this.categoryCode = categoryCode; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    public String getOriginDate() { return originDate; }
    public void setOriginDate(String originDate) { this.originDate = originDate; }
    public String getProcessDate() { return processDate; }
    public void setProcessDate(String processDate) { this.processDate = processDate; }
    public String getMerchantId() { return merchantId; }
    public void setMerchantId(String merchantId) { this.merchantId = merchantId; }
    public String getMerchantName() { return merchantName; }
    public void setMerchantName(String merchantName) { this.merchantName = merchantName; }
    public String getMerchantCity() { return merchantCity; }
    public void setMerchantCity(String merchantCity) { this.merchantCity = merchantCity; }
    public String getMerchantZip() { return merchantZip; }
    public void setMerchantZip(String merchantZip) { this.merchantZip = merchantZip; }
}
