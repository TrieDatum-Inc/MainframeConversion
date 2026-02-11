package com.carddemo.service;

import com.carddemo.dto.TransactionTypeUpdateRequest;
import com.carddemo.entity.TransactionCategory;
import com.carddemo.entity.TransactionType;
import com.carddemo.exception.ResourceNotFoundException;
import com.carddemo.repository.TransactionCategoryRepository;
import com.carddemo.repository.TransactionTypeRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class TransactionTypeService {

    private final TransactionTypeRepository transactionTypeRepository;
    private final TransactionCategoryRepository transactionCategoryRepository;

    public TransactionTypeService(TransactionTypeRepository transactionTypeRepository,
                                  TransactionCategoryRepository transactionCategoryRepository) {
        this.transactionTypeRepository = transactionTypeRepository;
        this.transactionCategoryRepository = transactionCategoryRepository;
    }

    public Page<TransactionType> listTransactionTypes(Pageable pageable) {
        return transactionTypeRepository.findAll(pageable);
    }

    public TransactionType getTransactionType(String typeCode) {
        return transactionTypeRepository.findById(typeCode)
                .orElseThrow(() -> new ResourceNotFoundException("Transaction type not found: " + typeCode));
    }

    public List<TransactionCategory> getCategoriesByType(String typeCode) {
        return transactionCategoryRepository.findByTypeCode(typeCode);
    }

    @Transactional
    public TransactionType updateTransactionType(String typeCode, TransactionTypeUpdateRequest request) {
        TransactionType type = transactionTypeRepository.findById(typeCode)
                .orElseThrow(() -> new ResourceNotFoundException("Transaction type not found: " + typeCode));

        type.setTypeDescription(request.getTypeDescription());
        return transactionTypeRepository.save(type);
    }
}
