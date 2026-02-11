package com.carddemo.controller;

import com.carddemo.dto.CardUpdateRequest;
import com.carddemo.entity.Card;
import com.carddemo.service.CardService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/cards")
@Tag(name = "Cards")
public class CardController {

    private final CardService cardService;

    public CardController(CardService cardService) {
        this.cardService = cardService;
    }

    @GetMapping
    @Operation(summary = "List credit cards (paginated)",
            description = "List all credit cards with optional account filter. " +
                    "Equivalent to COCRDLIC (Transaction CCLI). " +
                    "Reads from CARDDAT, CARDAIX files.")
    public ResponseEntity<Page<Card>> listCards(
            @Parameter(description = "Filter by account ID") @RequestParam(required = false) String accountId,
            @Parameter(description = "Page number (0-based)") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "10") int size) {
        Pageable pageable = PageRequest.of(page, size);
        return ResponseEntity.ok(cardService.listCards(accountId, pageable));
    }

    @GetMapping("/search")
    @Operation(summary = "Search credit cards",
            description = "Search cards by card number. " +
                    "Equivalent to COCRDSLC (Transaction CCDL). " +
                    "Reads from CARDDAT, CARDAIX files.")
    public ResponseEntity<List<Card>> searchCards(
            @Parameter(description = "Card number to search") @RequestParam String query) {
        return ResponseEntity.ok(cardService.searchCards(query));
    }

    @GetMapping("/{cardNumber}")
    @Operation(summary = "View card details",
            description = "Retrieve details for a specific credit card.")
    public ResponseEntity<Card> getCard(@PathVariable String cardNumber) {
        return ResponseEntity.ok(cardService.getCard(cardNumber));
    }

    @PutMapping("/{cardNumber}")
    @Operation(summary = "Update card details",
            description = "Update credit card information. " +
                    "Equivalent to COCRDUPC (Transaction CCUP). " +
                    "Updates CARDDAT file.")
    public ResponseEntity<Card> updateCard(
            @PathVariable String cardNumber, @RequestBody CardUpdateRequest request) {
        return ResponseEntity.ok(cardService.updateCard(cardNumber, request));
    }
}
