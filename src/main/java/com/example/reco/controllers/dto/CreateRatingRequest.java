package com.example.reco.controllers.dto;

import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

public class CreateRatingRequest {

    @NotNull(message = "userId is required")
    private Long userId;

    private BigDecimal grade;

    public CreateRatingRequest() {
    }

    public CreateRatingRequest(Long userId, BigDecimal grade) {
        this.userId = userId;
        this.grade = grade;
    }

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public BigDecimal getGrade() {
        return grade;
    }

    public void setGrade(BigDecimal grade) {
        this.grade = grade;
    }
}
