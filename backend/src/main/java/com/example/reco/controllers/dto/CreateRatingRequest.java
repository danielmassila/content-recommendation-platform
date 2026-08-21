package com.example.reco.controllers.dto;

import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

public class CreateRatingRequest {

    @NotNull(message = "grade is required")
    private BigDecimal grade;

    public CreateRatingRequest() {
    }

    public CreateRatingRequest(BigDecimal grade) {
        this.grade = grade;
    }

    public BigDecimal getGrade() {
        return grade;
    }

    public void setGrade(BigDecimal grade) {
        this.grade = grade;
    }
}
