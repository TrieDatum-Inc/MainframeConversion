package com.carddemo.service;

import com.carddemo.dto.AccountDetailDto;
import com.carddemo.dto.AccountUpdateRequest;
import com.carddemo.entity.Account;
import com.carddemo.entity.Card;
import com.carddemo.entity.CardXref;
import com.carddemo.entity.Customer;
import com.carddemo.exception.ResourceNotFoundException;
import com.carddemo.repository.AccountRepository;
import com.carddemo.repository.CardRepository;
import com.carddemo.repository.CardXrefRepository;
import com.carddemo.repository.CustomerRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class AccountService {

    private final AccountRepository accountRepository;
    private final CustomerRepository customerRepository;
    private final CardRepository cardRepository;
    private final CardXrefRepository cardXrefRepository;

    public AccountService(AccountRepository accountRepository, CustomerRepository customerRepository,
                          CardRepository cardRepository, CardXrefRepository cardXrefRepository) {
        this.accountRepository = accountRepository;
        this.customerRepository = customerRepository;
        this.cardRepository = cardRepository;
        this.cardXrefRepository = cardXrefRepository;
    }

    public AccountDetailDto getAccountDetail(String acctId) {
        Account account = accountRepository.findById(acctId)
                .orElseThrow(() -> new ResourceNotFoundException("Account ID NOT found..."));

        List<CardXref> xrefs = cardXrefRepository.findByAccountId(acctId);
        Customer customer = null;
        if (!xrefs.isEmpty()) {
            customer = customerRepository.findById(xrefs.get(0).getCustomerId()).orElse(null);
        }

        List<Card> cards = cardRepository.findByAccountId(acctId);

        return AccountDetailDto.fromEntities(account, customer, cards);
    }

    @Transactional
    public AccountDetailDto updateAccount(String acctId, AccountUpdateRequest request) {
        Account account = accountRepository.findById(acctId)
                .orElseThrow(() -> new ResourceNotFoundException("Account ID NOT found..."));

        if (request.getActiveStatus() != null) {
            account.setActiveStatus(request.getActiveStatus());
        }
        if (request.getCreditLimit() != null) {
            account.setCreditLimit(request.getCreditLimit());
        }
        if (request.getCashCreditLimit() != null) {
            account.setCashCreditLimit(request.getCashCreditLimit());
        }
        if (request.getExpirationDate() != null) {
            account.setExpirationDate(request.getExpirationDate());
        }
        if (request.getReissueDate() != null) {
            account.setReissueDate(request.getReissueDate());
        }
        if (request.getAddressZip() != null) {
            account.setAddressZip(request.getAddressZip());
        }
        if (request.getGroupId() != null) {
            account.setGroupId(request.getGroupId());
        }

        accountRepository.save(account);
        return getAccountDetail(acctId);
    }
}
