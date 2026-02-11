package com.carddemo.dto;

import com.carddemo.entity.Account;
import com.carddemo.entity.Customer;
import com.carddemo.entity.Card;
import java.math.BigDecimal;
import java.util.List;

public class AccountDetailDto {

    private String acctId;
    private String activeStatus;
    private BigDecimal currentBalance;
    private BigDecimal creditLimit;
    private BigDecimal cashCreditLimit;
    private String openDate;
    private String expirationDate;
    private String reissueDate;
    private BigDecimal currentCycleCredit;
    private BigDecimal currentCycleDebit;
    private String addressZip;
    private String groupId;
    private CustomerInfo customer;
    private List<CardInfo> cards;

    public static AccountDetailDto fromEntities(Account account, Customer customer, List<Card> cards) {
        AccountDetailDto dto = new AccountDetailDto();
        dto.setAcctId(account.getAcctId());
        dto.setActiveStatus(account.getActiveStatus());
        dto.setCurrentBalance(account.getCurrentBalance());
        dto.setCreditLimit(account.getCreditLimit());
        dto.setCashCreditLimit(account.getCashCreditLimit());
        dto.setOpenDate(account.getOpenDate());
        dto.setExpirationDate(account.getExpirationDate());
        dto.setReissueDate(account.getReissueDate());
        dto.setCurrentCycleCredit(account.getCurrentCycleCredit());
        dto.setCurrentCycleDebit(account.getCurrentCycleDebit());
        dto.setAddressZip(account.getAddressZip());
        dto.setGroupId(account.getGroupId());

        if (customer != null) {
            CustomerInfo ci = new CustomerInfo();
            ci.setCustId(customer.getCustId());
            ci.setFirstName(customer.getFirstName());
            ci.setMiddleName(customer.getMiddleName());
            ci.setLastName(customer.getLastName());
            ci.setSsn(customer.getSsn());
            ci.setDateOfBirth(customer.getDateOfBirth());
            ci.setFicoCreditScore(customer.getFicoCreditScore());
            ci.setAddressLine1(customer.getAddressLine1());
            ci.setAddressLine2(customer.getAddressLine2());
            ci.setAddressLine3(customer.getAddressLine3());
            ci.setStateCode(customer.getStateCode());
            ci.setCountryCode(customer.getCountryCode());
            ci.setZip(customer.getZip());
            ci.setPhoneNum1(customer.getPhoneNum1());
            ci.setPhoneNum2(customer.getPhoneNum2());
            dto.setCustomer(ci);
        }

        if (cards != null) {
            dto.setCards(cards.stream().map(c -> {
                CardInfo cardInfo = new CardInfo();
                cardInfo.setCardNumber(c.getCardNumber());
                cardInfo.setEmbossedName(c.getEmbossedName());
                cardInfo.setExpirationDate(c.getExpirationDate());
                cardInfo.setActiveStatus(c.getActiveStatus());
                return cardInfo;
            }).toList());
        }

        return dto;
    }

    public String getAcctId() { return acctId; }
    public void setAcctId(String acctId) { this.acctId = acctId; }
    public String getActiveStatus() { return activeStatus; }
    public void setActiveStatus(String activeStatus) { this.activeStatus = activeStatus; }
    public BigDecimal getCurrentBalance() { return currentBalance; }
    public void setCurrentBalance(BigDecimal currentBalance) { this.currentBalance = currentBalance; }
    public BigDecimal getCreditLimit() { return creditLimit; }
    public void setCreditLimit(BigDecimal creditLimit) { this.creditLimit = creditLimit; }
    public BigDecimal getCashCreditLimit() { return cashCreditLimit; }
    public void setCashCreditLimit(BigDecimal cashCreditLimit) { this.cashCreditLimit = cashCreditLimit; }
    public String getOpenDate() { return openDate; }
    public void setOpenDate(String openDate) { this.openDate = openDate; }
    public String getExpirationDate() { return expirationDate; }
    public void setExpirationDate(String expirationDate) { this.expirationDate = expirationDate; }
    public String getReissueDate() { return reissueDate; }
    public void setReissueDate(String reissueDate) { this.reissueDate = reissueDate; }
    public BigDecimal getCurrentCycleCredit() { return currentCycleCredit; }
    public void setCurrentCycleCredit(BigDecimal currentCycleCredit) { this.currentCycleCredit = currentCycleCredit; }
    public BigDecimal getCurrentCycleDebit() { return currentCycleDebit; }
    public void setCurrentCycleDebit(BigDecimal currentCycleDebit) { this.currentCycleDebit = currentCycleDebit; }
    public String getAddressZip() { return addressZip; }
    public void setAddressZip(String addressZip) { this.addressZip = addressZip; }
    public String getGroupId() { return groupId; }
    public void setGroupId(String groupId) { this.groupId = groupId; }
    public CustomerInfo getCustomer() { return customer; }
    public void setCustomer(CustomerInfo customer) { this.customer = customer; }
    public List<CardInfo> getCards() { return cards; }
    public void setCards(List<CardInfo> cards) { this.cards = cards; }

    public static class CustomerInfo {
        private String custId;
        private String firstName;
        private String middleName;
        private String lastName;
        private String ssn;
        private String dateOfBirth;
        private Integer ficoCreditScore;
        private String addressLine1;
        private String addressLine2;
        private String addressLine3;
        private String stateCode;
        private String countryCode;
        private String zip;
        private String phoneNum1;
        private String phoneNum2;

        public String getCustId() { return custId; }
        public void setCustId(String custId) { this.custId = custId; }
        public String getFirstName() { return firstName; }
        public void setFirstName(String firstName) { this.firstName = firstName; }
        public String getMiddleName() { return middleName; }
        public void setMiddleName(String middleName) { this.middleName = middleName; }
        public String getLastName() { return lastName; }
        public void setLastName(String lastName) { this.lastName = lastName; }
        public String getSsn() { return ssn; }
        public void setSsn(String ssn) { this.ssn = ssn; }
        public String getDateOfBirth() { return dateOfBirth; }
        public void setDateOfBirth(String dateOfBirth) { this.dateOfBirth = dateOfBirth; }
        public Integer getFicoCreditScore() { return ficoCreditScore; }
        public void setFicoCreditScore(Integer ficoCreditScore) { this.ficoCreditScore = ficoCreditScore; }
        public String getAddressLine1() { return addressLine1; }
        public void setAddressLine1(String addressLine1) { this.addressLine1 = addressLine1; }
        public String getAddressLine2() { return addressLine2; }
        public void setAddressLine2(String addressLine2) { this.addressLine2 = addressLine2; }
        public String getAddressLine3() { return addressLine3; }
        public void setAddressLine3(String addressLine3) { this.addressLine3 = addressLine3; }
        public String getStateCode() { return stateCode; }
        public void setStateCode(String stateCode) { this.stateCode = stateCode; }
        public String getCountryCode() { return countryCode; }
        public void setCountryCode(String countryCode) { this.countryCode = countryCode; }
        public String getZip() { return zip; }
        public void setZip(String zip) { this.zip = zip; }
        public String getPhoneNum1() { return phoneNum1; }
        public void setPhoneNum1(String phoneNum1) { this.phoneNum1 = phoneNum1; }
        public String getPhoneNum2() { return phoneNum2; }
        public void setPhoneNum2(String phoneNum2) { this.phoneNum2 = phoneNum2; }
    }

    public static class CardInfo {
        private String cardNumber;
        private String embossedName;
        private String expirationDate;
        private String activeStatus;

        public String getCardNumber() { return cardNumber; }
        public void setCardNumber(String cardNumber) { this.cardNumber = cardNumber; }
        public String getEmbossedName() { return embossedName; }
        public void setEmbossedName(String embossedName) { this.embossedName = embossedName; }
        public String getExpirationDate() { return expirationDate; }
        public void setExpirationDate(String expirationDate) { this.expirationDate = expirationDate; }
        public String getActiveStatus() { return activeStatus; }
        public void setActiveStatus(String activeStatus) { this.activeStatus = activeStatus; }
    }
}
