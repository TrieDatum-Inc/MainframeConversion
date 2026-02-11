package com.carddemo.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class TransactionTypeUpdateRequest {

    @NotBlank(message = "Type description is required")
    @Size(max = 50, message = "Type description must be at most 50 characters")
    private String typeDescription;

    public String getTypeDescription() { return typeDescription; }
    public void setTypeDescription(String typeDescription) { this.typeDescription = typeDescription; }
}
