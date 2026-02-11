package com.carddemo.repository;

import com.carddemo.entity.Card;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CardRepository extends JpaRepository<Card, String> {

    Page<Card> findByAccountId(String accountId, Pageable pageable);

    List<Card> findByAccountId(String accountId);

    List<Card> findByCardNumberContaining(String cardNumber);
}
