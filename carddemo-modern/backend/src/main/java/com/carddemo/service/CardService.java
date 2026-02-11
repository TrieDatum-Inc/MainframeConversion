package com.carddemo.service;

import com.carddemo.dto.CardUpdateRequest;
import com.carddemo.entity.Card;
import com.carddemo.exception.ResourceNotFoundException;
import com.carddemo.repository.CardRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class CardService {

    private final CardRepository cardRepository;

    public CardService(CardRepository cardRepository) {
        this.cardRepository = cardRepository;
    }

    public Page<Card> listCards(String accountId, Pageable pageable) {
        if (accountId != null && !accountId.isBlank()) {
            return cardRepository.findByAccountId(accountId, pageable);
        }
        return cardRepository.findAll(pageable);
    }

    public Card getCard(String cardNumber) {
        return cardRepository.findById(cardNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Card Number NOT found..."));
    }

    public List<Card> searchCards(String query) {
        return cardRepository.findByCardNumberContaining(query);
    }

    @Transactional
    public Card updateCard(String cardNumber, CardUpdateRequest request) {
        Card card = cardRepository.findById(cardNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Card Number NOT found..."));

        if (request.getEmbossedName() != null) {
            card.setEmbossedName(request.getEmbossedName());
        }
        if (request.getExpirationDate() != null) {
            card.setExpirationDate(request.getExpirationDate());
        }
        if (request.getActiveStatus() != null) {
            card.setActiveStatus(request.getActiveStatus());
        }

        return cardRepository.save(card);
    }
}
