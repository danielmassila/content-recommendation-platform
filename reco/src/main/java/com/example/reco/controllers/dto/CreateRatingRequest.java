package com.example.reco.controllers.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public class CreateRatingRequest {

    @NotNull(message = "userId is required")
    private Long userId;

    @NotNull(message = "grade is required")
    @Min(value = 1, message = "grade must be between 1 and 5")
    @Max(value = 5, message = "grade must be between 1 and 5")
    private Short grade;

    public CreateRatingRequest() {
    }

    public CreateRatingRequest(Long userId, Short grade) {
        this.userId = userId;
        this.grade = grade;
    }

    public Long getUserId() {
        return userId;
    }

    public Short getGrade() {
        return grade;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public void setGrade(Short grade) {
        this.grade = grade;
    }
}
